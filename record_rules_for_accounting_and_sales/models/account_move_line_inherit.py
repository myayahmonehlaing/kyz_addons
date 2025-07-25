from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related='move_id.department_id',
        store=True,
        readonly=True,
    )