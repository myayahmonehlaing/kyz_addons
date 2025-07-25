# in models/account_payment.py
from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    reservation_ids = fields.Many2many(
        'hotel.reservation',
        string='Related Reservations',
        compute='_compute_reservation_ids',
        store=True
    )

    @api.depends('reconciled_invoice_ids.reservation_id')
    def _compute_reservation_ids(self):
        for payment in self:
            reservations = payment.reconciled_invoice_ids.mapped('reservation_id')
            payment.reservation_ids = [(6, 0, reservations.ids)]