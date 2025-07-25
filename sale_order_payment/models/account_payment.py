from odoo import models, fields

class AccountPayment(models.Model):
    """
    Inherit account.payment to add a link to the sale.order model.
    """
    _inherit = 'account.payment'

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        help="Sale Order for which this payment is made.",
        ondelete='set null',
        copy=False,
    )
    matched_invoice_ids = fields.Many2many(
        string="Matched Invoices",
        comodel_name='account.move',
        relation='account_move_payment_rel',
        column1='payment_id',
        column2='move_id',
        copy=False,
    )