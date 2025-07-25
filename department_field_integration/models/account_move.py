from odoo import models, fields


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    department_id = fields.Many2one('hr.department', string='Department', ondelete='set null')