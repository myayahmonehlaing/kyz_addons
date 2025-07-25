
from odoo import _ ,models, fields, api
from odoo.tools import frozendict


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # adding field
    fix_discount = fields.Float(
        string='Fix Discount',
        digits='Discount',
        default=0.0,
        help="Fixed discount amount (in currency) for this invoice line"
    )

    # #adding fix_discount to selection
    # display_type = fields.Selection(
    #     selection_add=[('fix_discount', "Fix Discount")],
    #     ondelete={'fix_discount': 'cascade'},
    # )

    @api.depends('quantity', 'discount', 'fix_discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        super()._compute_totals()


    @api.depends('account_id', 'company_id', 'discount', 'fix_discount', 'price_unit', 'quantity', 'currency_rate')
    def _compute_discount_allocation_needed(self):
        for line in self:
            line.discount_allocation_dirty = True
            discount_allocation_account = line.move_id._get_discount_allocation_account()

            # if not discount_allocation_account or line.display_type != 'product' or line.currency_id.is_zero(line.discount):
            #     line.discount_allocation_needed = False
            #     continue

            if (not discount_allocation_account
                    or line.display_type != 'product'
                    or (line.currency_id.is_zero(line.discount) and line.currency_id.is_zero(line.fix_discount))):
                line.discount_allocation_needed = False
                continue

            fix_discount_amount = line.quantity * line.fix_discount
            percent_discount_amount = ((line.quantity * line.price_unit) - fix_discount_amount) * line.discount/100

            discounted_amount_currency = line.currency_id.round(line.move_id.direction_sign * (percent_discount_amount + fix_discount_amount))

            discount_allocation_needed = {}
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'account_id': line.account_id.id,
                    'move_id': line.move_id.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] += discounted_amount_currency
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'move_id': line.move_id.id,
                    'account_id': discount_allocation_account.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] -= discounted_amount_currency
            line.discount_allocation_needed = {k: frozendict(v) for k, v in discount_allocation_needed.items()}


    def _prepare_edi_vals_to_export(self):
        self.ensure_one()

        # >>> ADDED: Apply fix_discount before applying percent discount
        effective_price_unit = max(self.price_unit - (self.fix_discount or 0.0), 0.0)  # >>> ADDED
        price_unit_after_discount = effective_price_unit * (1 - (self.discount or 0.0) / 100.0)  # >>> CHANGED

        # >>> CHANGED: Gross subtotal logic considers both fix and percent discount
        if self.discount == 100.0 and not self.fix_discount:
            gross_price_subtotal = self.currency_id.round(self.price_unit * self.quantity)
        else:
            gross_price_subtotal = self.currency_id.round(price_unit_after_discount * self.quantity)

        res = {
            'line': self,
            'price_unit_after_discount': self.currency_id.round(price_unit_after_discount),  # >>> CHANGED
            'price_subtotal_before_discount': gross_price_subtotal,
            'price_subtotal_unit': self.currency_id.round(
                self.price_subtotal / self.quantity) if self.quantity else 0.0,
            'price_total_unit': self.currency_id.round(self.price_total / self.quantity) if self.quantity else 0.0,
            'price_discount': gross_price_subtotal - self.price_subtotal,
            'price_discount_unit': (
                (gross_price_subtotal - self.price_subtotal) / self.quantity
                if self.quantity else 0.0
            ),
            'gross_price_total_unit': self.currency_id.round(
                gross_price_subtotal / self.quantity
            ) if self.quantity else 0.0,
            'unece_uom_code': self.product_id.product_tmpl_id.uom_id._get_unece_code(),
        }
        return res


    ### From sale order module
    def _sale_prepare_sale_line_values(self, order, price):
        """ Generate the sale.line creation value from the current move line """
        self.ensure_one()
        last_so_line = self.env['sale.order.line'].search([('order_id', '=', order.id)], order='sequence desc', limit=1)
        last_sequence = last_so_line.sequence + 1 if last_so_line else 100

        fpos = order.fiscal_position_id or order.fiscal_position_id._get_fiscal_position(order.partner_id)
        product_taxes = self.product_id.taxes_id._filter_taxes_by_company(order.company_id)
        taxes = fpos.map_tax(product_taxes)

        return {
            'order_id': order.id,
            'name': self.name,
            'sequence': last_sequence,
            'price_unit': price,
            'tax_id': [x.id for x in taxes],
            'discount': 0.0,
            'fix_discount' : 0.0,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.quantity,
            'is_expense': True,
        }
