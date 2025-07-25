from odoo import models, fields


# Optional: A model for categorizing services (e.g., "Food & Beverage", "Wellness", "Business")
class HotelServiceType(models.Model):
    _name = 'hotel.service.type'
    _description = 'Hotel Service Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
