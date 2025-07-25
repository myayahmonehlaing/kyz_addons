from odoo import models, fields

class HotelAmenityType(models.Model):
    _name = 'hotel.amenity.type'
    _description = 'Amenity Type'

    name = fields.Char(string="Amenity Type", required=True)

    description = fields.Text(string="Description")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)