# in models/hotel_room_template_line.py
from odoo import models, fields

class HotelRoomTemplateLine(models.Model):
    """
    A template line to define a default service and quantity for a room type.
    This is a CONFIGURATION model, not a transactional one.
    """
    _name = 'hotel.room.template.line'
    _description = 'Room Service Template Line'

    # Link back to the room this template line belongs to
    room_id = fields.Many2one('hotel.room', string='Room', required=True, ondelete='cascade')
    # The service to be included in the template
    service_id = fields.Many2one('hotel.service', string='Service', required=True)
    quantity = fields.Float(string='Default Quantity', default=1.0, required=True)

    # Helper fields for a better user interface in the room form
    price = fields.Float(related='service_id.list_price', string='Price', readonly=True)
    currency_id = fields.Many2one(related='service_id.currency_id', readonly=True)