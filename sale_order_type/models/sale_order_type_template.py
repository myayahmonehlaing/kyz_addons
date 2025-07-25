
from odoo import models, fields, api


class SaleOrderTypeTemplate(models.Model):
    _name = 'sale.order.type.template'
    _description = 'Sale Order Type Template'
    _check_company_auto = True


    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    sequence_id = fields.Many2one("ir.sequence", ondelete='set null')
    warehouse_id = fields.Many2one("stock.warehouse", ondelete='set null')
    journal_id = fields.Many2one("account.journal", ondelete='set null', domain=[('type', '=', 'sale')])
    # auto_invoice = fields.Boolean()
    # auto_picking_done = fields.Boolean()
