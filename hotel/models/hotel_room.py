# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _inherits = {'product.product': 'product_id'}

    # Fields from the specification
    name = fields.Char(comodel_name='product.name',
                       readonly=False, string='Room Number', required=True)
    # We explicitly define 'name' to satisfy the validation rule.
    # 'related' tells Odoo this is not a new field, but a pointer to the product's name.
    # 'readonly=False' is critical, as it allows us to SET the name from the room form.

    category_id = fields.Many2one('hotel.room.type', string='Category', required=True)
    building_id = fields.Many2one('hotel.building', string='Building', required=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor', required=True)
    # product_id = fields.Many2one('product.product', string='Product', readonly=True, copy=False)
    product_id = fields.Many2one(
        'product.product',
        string='Product Room',
        required=True,
        ondelete='cascade',
        auto_join=True,
        help="The product related to this room."
    )

    taxes_id = fields.Many2many(
        'account.tax',
        related='product_id.taxes_id',
        string="Taxes",
        readonly=False,
        check_company=True
    )

    capacity = fields.Integer(string='Capacity', default=1)
    description = fields.Text(string='Description')
    list_price = fields.Float(string='Price')
    state = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Maintenance')
    ], string='Room Status', default='available', required=True)
    # company_id = fields.Many2one('res.company', string='Company',
    #                              related='floor_id.building_id.company_id', store=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)


    amenity_ids = fields.Many2many(
        'hotel.amenity',
        'hotel_room_amenity_rel',  # relation table
        'room_id',
        'amenity_id',
        string='Amenities'
    )

    reservation_line_ids = fields.One2many(
        'hotel.reservation.line',
        'room_id',
        string='Reservations',
        compute='_compute_reservation_lines',
        store=False,
    )

    def _compute_reservation_lines(self):
        for room in self:
            room.reservation_line_ids = self.env['hotel.reservation.line'].search([
                ('room_id', '=', room.id)
            ])

    # Helper to prepare product values
    def _prepare_product_vals(self, room_vals):
        return {
            'name': room_vals.get('name'),
            'type': 'service',  # hotel rooms are services, not storable products
            'list_price': room_vals.get('list_price'),
            'invoice_policy': 'order',
            'categ_id': self.env.ref('product.product_category_all').id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        Product = self.env['product.product']
        for vals in vals_list:
            if not vals.get('product_id'):
                product_vals = self._prepare_product_vals(vals)
                new_product = Product.create(product_vals)
                vals['product_id'] = new_product.id
        return super().create(vals_list)

    # ///////////////////////////////// Dummy Data Creation ////////////////////////////////////
    # @api.model_create_multi
    # def create(self, vals_list):
    #     Product = self.env['product.product']
    #     Reservation = self.env['hotel.reservation']
    #     ReservationLine = self.env['hotel.reservation.line']
    #
    #     # Get or create dummy reservation
    #     dummy_res = Reservation.search([('name', '=', 'DUMMY')], limit=1)
    #     if not dummy_res:
    #         dummy_res = Reservation.create({
    #             'name': 'DUMMY',
    #             'partner_id': self.env.ref('base.public_partner').id,
    #             'status': 'draft',
    #         })
    #
    #     # Pre-process product creation
    #     for vals in vals_list:
    #         if not vals.get('product_id'):
    #             if not vals.get('name'):
    #                 raise ValueError("Room 'name' is required to create the product.")
    #             product_vals = {
    #                 'name': vals['name'],
    #                 'type': 'service',
    #                 'list_price': vals.get('list_price', 0.0),
    #                 'invoice_policy': 'order',
    #                 'categ_id': self.env.ref('product.product_category_all').id,
    #             }
    #             product = Product.create(product_vals)
    #             vals['product_id'] = product.id
    #
    #     rooms = super().create(vals_list)
    #
    #     checkin_date = datetime(2025, 1, 6, 12, 0, 0)
    #     checkout_date = datetime(2025, 1, 8, 12, 0, 0)
    #
    #     # Create dummy reservation lines
    #     for room in rooms:
    #         ReservationLine.create({
    #             'reservation_id': dummy_res.id,
    #             'room_id': room.id,
    #
    #             'checkin_date': checkin_date,
    #             'checkout_date': checkout_date,
    #             'unit_price': 0.0,
    #             'is_dummy': True,
    #             'partner_id': dummy_res.partner_id.id,
    #         })

        # return rooms
    # 'checkin_date': datetime.now() - timedelta(days=365),
    # 'checkout_date': datetime.now() - timedelta(days=364, minutes=55),

# /////////////////////////////////////////////////////////////////////////////////////////
#     def _get_dummy_reservation(self):
#         Reservation = self.env['hotel.reservation']
#         dummy_name = 'Auto Dummy Reservation'
#         dummy_reservation = Reservation.search([('name', '=', dummy_name)], limit=1)
#         if not dummy_reservation:
#             # Create dummy reservation with today and tomorrow as dates
#             today = fields.Date.context_today(self)
#             tomorrow = fields.Date.to_date(today) + timedelta(days=1) if isinstance(today, str) else today + timedelta(
#                 days=1)
#             dummy_reservation = Reservation.create({
#                 'name': dummy_name,
#                 'partner_id': self.env.ref('base.res_partner_1').id,  # Or your default partner
#                 'checkin_date': today,
#                 'checkout_date': tomorrow,
#                 'status': 'confirmed',
#             })
#         return dummy_reservation
#
# from datetime import timedelta
#
# class HotelRoom(models.Model):
#     _inherit = 'hotel.room'  # or _name if full model code
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         rooms = super().create(vals_list)
#         dummy_reservation = self._get_dummy_reservation()
#         today = fields.Datetime.now()
#         tomorrow = today + timedelta(days=1)
#
#         ReservationLine = self.env['hotel.reservation.line']
#
#         for room in rooms:
#             existing = ReservationLine.search([
#                 ('room_id', '=', room.id),
#                 ('reservation_id', '=', dummy_reservation.id),
#             ], limit=1)
#             if not existing:
#                 ReservationLine.create({
#                     'name': f'{room.name} - Dummy',
#                     'room_id': room.id,
#                     'checkin_date': today,
#                     'checkout_date': tomorrow,
#                     'unit_price': room.list_price or 100.0,
#                     'reservation_id': dummy_reservation.id,
#                 })
#         return rooms
#
#     def write(self, vals):
#         res = super().write(vals)
#         dummy_reservation = self._get_dummy_reservation()
#         today = fields.Datetime.now()
#         tomorrow = today + timedelta(days=1)
#
#         ReservationLine = self.env['hotel.reservation.line']
#
#         for room in self:
#             existing = ReservationLine.search([
#                 ('room_id', '=', room.id),
#                 ('reservation_id', '=', dummy_reservation.id),
#             ], limit=1)
#             if not existing:
#                 ReservationLine.create({
#                     'name': f'{room.name} - Dummy',
#                     'room_id': room.id,
#                     'checkin_date': today,
#                     'checkout_date': tomorrow,
#                     'unit_price': room.list_price or 100.0,
#                     'reservation_id': dummy_reservation.id,
#                 })
#         return res
