from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="Sale Order reference for reconciliation purposes",
        copy=False,
        index=True
    )