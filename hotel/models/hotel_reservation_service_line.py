# in models/hotel_reservation_service.py
from odoo import models, fields, api
from odoo.tools import float_round

class HotelReservationService(models.Model):
    _name = 'hotel.reservation.service'
    _description = 'Reservation Service Line'

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation', ondelete='cascade', required=True)

    # service_id = fields.Many2one(
    #     'product.product',
    #     string='Service',
    #     required=True,
    #     domain="[('type', '=', 'service')]"
    # )

    service_id = fields.Many2one('hotel.service', string='Service', required=True)
    service_taxes_id = fields.Many2many(
        related='service_id.taxes_id',
        string="Taxes",
        readonly=False
    )

    # service_id = fields.Many2one(
    #     'product.product',
    #     string='Service',
    #     required=True,
    #     # This domain filters the list to only show products that have a corresponding hotel.service entry.
    #     domain="[('hotel_service_id', '!=', False)]",
    #     help="Only services defined in the Hotel > Configuration > Hotel Services menu are shown here."
    # )
    quantity = fields.Integer(string='Quantity', default=1)
    price_unit = fields.Float(string='Unit Price')

    subtotal = fields.Monetary(string='Total', compute='_compute_subtotal', store=True)

    currency_id = fields.Many2one(related='reservation_id.currency_id', store=True)

    company_id = fields.Many2one(related='reservation_id.company_id', store=True)

    partner_id = fields.Many2one(related='reservation_id.partner_id', store=True)

    # @api.depends('quantity', 'price_unit')
    # def _compute_subtotal(self):
    #     for line in self:
    #         line.subtotal = line.quantity * line.price_unit

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.price_unit = self.service_id.list_price


    @api.depends('quantity', 'price_unit', 'service_taxes_id')
    def _compute_subtotal(self):
        for line in self:
            taxes = line.service_taxes_id
            currency = line.currency_id or line.reservation_id.currency_id
            price = line.price_unit * line.quantity

            if taxes:
                tax_results = taxes.compute_all(
                    line.price_unit,
                    currency=currency,
                    quantity=line.quantity,
                    product=None,
                    partner=line.reservation_id.partner_id
                )
                line.subtotal = float_round(tax_results['total_included'], precision_rounding=currency.rounding)
            else:
                line.subtotal = price

                # ???????????????????????????????????????? Tax for report

    tax_amount = fields.Monetary(string='Tax Amount', compute='_compute_tax_amount', store=True)

    @api.depends('quantity', 'price_unit', 'service_taxes_id', 'reservation_id.partner_id')
    def _compute_tax_amount(self):
        for line in self:
            taxes = line.service_taxes_id
            currency = line.currency_id or line.reservation_id.currency_id
            if taxes:
                tax_results = taxes.compute_all(
                    line.price_unit,
                    currency=currency,
                    quantity=line.quantity,
                    product=None,
                    partner=line.reservation_id.partner_id
                )
                line.tax_amount = tax_results['total_included'] - tax_results['total_excluded']
            else:
                line.tax_amount = 0.0