from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    reservation_id = fields.Many2one('hotel.reservation', string='Hotel Reservation', readonly=True)
