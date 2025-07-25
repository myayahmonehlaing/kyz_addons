from odoo import models, fields


class HotelAmenity(models.Model):
    _name = 'hotel.amenity'
    _description = 'Room Amenity'

    name = fields.Char(string="Amenity Name", required=True)

    amenity_type_id = fields.Many2one('hotel.amenity.type', string="Amenity Type", required=True)
    description = fields.Text(string="Description")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # room_id = fields.Many2one('hotel.room', string='Room')