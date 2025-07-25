from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    template_id = fields.Many2one(
        'sale.order.type.template',
        string='Default Sales Template'
    )
