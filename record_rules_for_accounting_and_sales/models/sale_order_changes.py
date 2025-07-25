from odoo import models, fields, api

class SaleOrderChanges(models.Model):
    _inherit = 'sale.order'

    department_id = fields.Many2one(comodel_name='hr.department', string="Department")


    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res['department_id'] = self.department_id.id
        return res
