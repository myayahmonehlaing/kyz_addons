from odoo import models, fields

class SaleReportInherit(models.Model):
    _inherit = 'sale.report'

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        readonly=True
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['department_id'] = "department_id"
        return res

    def _group_by_additional_fields(self):
        res = super()._group_by_additional_fields()
        res.append('department_id')
        return res
