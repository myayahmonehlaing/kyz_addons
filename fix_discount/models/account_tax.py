
from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'


    @api.model
    def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
        """
        Inherit this helper to add `fix_discount` to the standard data structure.
        """
        base_line = super()._prepare_base_line_for_taxes_computation(record, **kwargs)
        def load(field, fallback):
            return self._get_base_line_field_value_from_record(record, field, kwargs, fallback)
        base_line['fix_discount'] = load('fix_discount', 0.0)
        return base_line

    # @api.model
    # def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
    #     """
    #     This is the corrected version that applies the fixed discount BEFORE the percentage discount.
    #     """
    #     # Store original price_unit to restore it later.
    #     original_price_unit = base_line['price_unit']
    #     # --- Your Required Calculation Logic ---
    #     # 1. Calculate the fixed discount on a per-unit basis.
    #     fix_discount_per_unit = 0.0
    #     if base_line.get('quantity') and base_line['quantity'] != 0:
    #         fix_discount_per_unit = base_line.get('fix_discount', 0.0) / base_line['quantity']
    #
    #     # 2. Calculate the new "effective" price unit by subtracting the fixed discount.
    #     # This new price will be the base for the standard percentage discount.
    #     effective_price_unit = original_price_unit - fix_discount_per_unit
    #
    #     # --- Prepare for the Super Call ---
    #     # We modify the `base_line` dictionary. The original Odoo function will now use this
    #     # new, reduced price unit as the base for applying the standard percentage discount.
    #     base_line['price_unit'] = effective_price_unit
    #
    #     try:
    #         # Call the original function. It will now perform:
    #         # effective_price_unit * (1 - discount / 100.0)
    #         # which is exactly what you want. It will then handle all currency
    #         # conversion and rounding on that result.
    #         super()._add_tax_details_in_base_line(base_line, company, rounding_method=rounding_method)
    #     finally:
    #         # Restore the original price_unit to avoid side effects.
    #         base_line['price_unit'] = original_price_unit

    @api.model
    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):

        price_unit_after_discount = base_line['price_unit'] - (base_line['fix_discount'])
        price_unit_after_discount = price_unit_after_discount  * (1 - (base_line['discount'] / 100.0))


        taxes_computation = base_line['tax_ids']._get_tax_details(
            price_unit=price_unit_after_discount,
            quantity=base_line['quantity'],
            precision_rounding=base_line['currency_id'].rounding,
            rounding_method=rounding_method or company.tax_calculation_rounding_method,
            product=base_line['product_id'],
            special_mode=base_line['special_mode'],
            manual_tax_amounts=base_line['manual_tax_amounts'],
        )
        rate = base_line['rate']
        tax_details = base_line['tax_details'] = {
            'raw_total_excluded_currency': taxes_computation['total_excluded'],
            'raw_total_excluded': taxes_computation['total_excluded'] / rate if rate else 0.0,
            'raw_total_included_currency': taxes_computation['total_included'],
            'raw_total_included': taxes_computation['total_included'] / rate if rate else 0.0,
            'taxes_data': [],
        }
        if company.tax_calculation_rounding_method == 'round_per_line':
            tax_details['raw_total_excluded'] = company.currency_id.round(tax_details['raw_total_excluded'])
            tax_details['raw_total_included'] = company.currency_id.round(tax_details['raw_total_included'])
        for tax_data in taxes_computation['taxes_data']:
            tax_amount = tax_data['tax_amount'] / rate if rate else 0.0
            base_amount = tax_data['base_amount'] / rate if rate else 0.0
            if company.tax_calculation_rounding_method == 'round_per_line':
                tax_amount = company.currency_id.round(tax_amount)
                base_amount = company.currency_id.round(base_amount)
            tax_details['taxes_data'].append({
                **tax_data,
                'raw_tax_amount_currency': tax_data['tax_amount'],
                'raw_tax_amount': tax_amount,
                'raw_base_amount_currency': tax_data['base_amount'],
                'raw_base_amount': base_amount,
            })


    @api.model
    def _dispatch_negative_lines(self, base_lines, sorting_criteria=None, additional_dispatching_method=None):
        """
        Dispatch negative lines onto positive ones, turning them into discounts (including fix_discount).
        """

        def dispatch_tax_amounts(neg_base_line, candidate, is_zero):
            def get_tax_key(tax_data):
                return frozendict({'tax': tax_data['tax'], 'is_reverse_charge': tax_data['is_reverse_charge']})

            base_line_fields = (
                'raw_total_excluded_currency', 'raw_total_excluded',
                'raw_total_included_currency', 'raw_total_included'
            )
            tax_data_fields = (
                'raw_base_amount_currency', 'raw_base_amount',
                'raw_tax_amount_currency', 'raw_tax_amount'
            )

            if is_zero:
                for field in base_line_fields:
                    candidate['tax_details'][field] += neg_base_line['tax_details'][field]
                    neg_base_line['tax_details'][field] = 0.0
            else:
                for field in base_line_fields:
                    neg_base_line['tax_details'][field] += candidate['tax_details'][field]
                    candidate['tax_details'][field] = 0.0

            for tax_data in neg_base_line['tax_details']['taxes_data']:
                tax_key = get_tax_key(tax_data)
                other_tax_data = next(
                    x for x in candidate['tax_details']['taxes_data'] if get_tax_key(x) == tax_key
                )
                if is_zero:
                    for field in tax_data_fields:
                        other_tax_data[field] += tax_data[field]
                        tax_data[field] = 0.0
                else:
                    for field in tax_data_fields:
                        tax_data[field] += other_tax_data[field]
                        other_tax_data[field] = 0.0

        results = {
            'result_lines': [],
            'orphan_negative_lines': [],
            'nulled_candidate_lines': [],
        }

        for line in base_lines:
            line.setdefault('discount_amount', line['discount_amount_before_dispatching'])
            # >>> ADDED:  fix_discount_amount
            line.setdefault('fix_discount_amount', line.get('fix_discount_amount_before_dispatching', 0.0))

            if line['currency_id'].compare_amounts(line['gross_price_subtotal'], 0) < 0.0:
                results['orphan_negative_lines'].append(line)
            else:
                results['result_lines'].append(line)

        for neg_base_line in list(results['orphan_negative_lines']):
            candidates = [
                candidate
                for candidate in results['result_lines']
                if (
                    neg_base_line['currency_id'] == candidate['currency_id']
                    and neg_base_line['partner_id'] == candidate['partner_id']
                    and neg_base_line['tax_ids'] == candidate['tax_ids']
                )
            ]

            sorting_criteria = sorting_criteria or self._get_negative_lines_sorting_candidate_criteria()
            sorted_candidates = sorted(
                candidates,
                key=lambda candidate: tuple(method(candidate, neg_base_line) for method in sorting_criteria)
            )

            for candidate in sorted_candidates:
                net_price_subtotal = neg_base_line['gross_price_subtotal'] \
                                     - neg_base_line['discount_amount'] \
                                     - neg_base_line.get('fix_discount_amount', 0.0)

                other_net_price_subtotal = candidate['gross_price_subtotal'] \
                                           - candidate['discount_amount'] \
                                           - candidate.get('fix_discount_amount', 0.0)

                discount_to_distribute = min(other_net_price_subtotal, -net_price_subtotal)
                if candidate['currency_id'].is_zero(discount_to_distribute):
                    continue

                # >>> ADDED: Split equally across discount and fix_discount if both are used
                # You may customize this logic further based on your dispatching rules
                candidate['discount_amount'] += discount_to_distribute / 2
                candidate['fix_discount_amount'] += discount_to_distribute / 2
                neg_base_line['discount_amount'] -= discount_to_distribute / 2
                neg_base_line['fix_discount_amount'] -= discount_to_distribute / 2

                remaining_to_distribute = neg_base_line['gross_price_subtotal'] \
                                          - neg_base_line['discount_amount'] \
                                          - neg_base_line.get('fix_discount_amount', 0.0)
                is_zero = neg_base_line['currency_id'].is_zero(remaining_to_distribute)

                dispatch_tax_amounts(neg_base_line, candidate, is_zero)
                if additional_dispatching_method:
                    additional_dispatching_method(neg_base_line, candidate, discount_to_distribute, is_zero)

                remaining_amount = (
                    candidate['discount_amount']
                    + candidate.get('fix_discount_amount', 0.0)
                    - candidate['gross_price_subtotal']
                )
                if candidate['currency_id'].is_zero(remaining_amount):
                    results['result_lines'].remove(candidate)
                    results['nulled_candidate_lines'].append(candidate)

                if is_zero:
                    results['orphan_negative_lines'].remove(neg_base_line)
                    break

        return results

