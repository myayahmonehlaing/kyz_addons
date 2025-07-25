from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    fix_discount = fields.Float(
        string='Fix Discount',
        digits='Discount',
        default=0.0,
    )

    # Add 'fix_discount' to the dependencies of _compute_amount.
    # This ensures that when you change the fixed discount, the line totals update instantly.
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'fix_discount')
    def _compute_amount(self):
        super()._compute_amount()
    # def _compute_amount(self):
    #     for line in self:
    #         base_line = line._prepare_base_line_for_taxes_computation()
    #         self.env['account.tax']._add_tax_details_in_base_line(base_line, line.company_id)
    #         line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
    #         line.price_total = base_line['tax_details']['raw_total_included_currency']
    #         line.price_tax = line.price_total - line.price_subtotal




    # This is the most important function for creating the invoice.
    def _prepare_invoice_line(self, **optional_values):

        # Call the original method to get all the standard values.
        res = super()._prepare_invoice_line(**optional_values)

        # Add `fix_discount` to the dictionary of values that will be used
        # to create the invoice line. This correctly passes the value.
        res['fix_discount'] = self.fix_discount

        return res
