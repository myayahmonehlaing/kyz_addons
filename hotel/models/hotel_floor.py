from odoo import models, fields


class HotelFloor(models.Model):
    _name = 'hotel.floor'
    _description = 'Hotel Floor'

    name = fields.Char(string='Floor Name', required=True)
    building_id = fields.Many2one('hotel.building', string='Building', required=True)
    # company_id = fields.Many2one('res.company', string='Company', required=True, related='building_id.company_id', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    room_ids = fields.One2many('hotel.room', 'floor_id', string='Rooms')
