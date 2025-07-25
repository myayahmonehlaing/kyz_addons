from odoo import models, fields


class HotelBuilding(models.Model):
    _name = 'hotel.building'
    _description = 'Hotel Building'

    name = fields.Char(string='Building Name', required=True)
    address = fields.Text(string='Address')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # for hierarchy managemet for room
    '''How it works:

    A Room has a Many2one field pointing to a Floor.

    A Floor has a Many2one field pointing to a Building.
    
    A Building stands on its own (but is linked to a Company).'''
    floor_ids = fields.One2many('hotel.floor', 'building_id', string='Floors')
