from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HotelReservationLine(models.Model):
    _name = 'hotel.reservation.line'
    _description = 'Hotel Reservation Line'

    name = fields.Char(compute='_compute_name')
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    checkin_date = fields.Datetime(string='Check-in', requird=True)
    checkout_date = fields.Datetime(string='Check-out', required=True)
    unit_price = fields.Float(string='Unit Price')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    room_taxes_id = fields.Many2many(
        related='room_id.taxes_id', string="Taxes", readonly=False, check_company=True)
    price_total = fields.Float(
        string="Total",
        compute='_compute_room_price',
        store=True)
    reservation_id = fields.Many2one('hotel.reservation', string='Reservation', ondelete='cascade')
    company_id = fields.Many2one(related='reservation_id.company_id', store=True)
    duration = fields.Integer(string='Duration (nights)', compute='_compute_duration', store=True)
    category_id = fields.Many2one(related='room_id.category_id', string='Room Type', required=True)

    reservation_status = fields.Selection(
        related='reservation_id.status',
        store=True,
        string="Reservation Status"
    )

    # partner_id = fields.Many2one('res.partner', string='Partner', readonly=False)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        compute='_compute_partner_id',
        inverse='_inverse_partner_id',
        store=True,
    )

    @api.depends('reservation_id.partner_id')
    def _compute_partner_id(self):
        for line in self:
            line.partner_id = line.reservation_id.partner_id

    def _inverse_partner_id(self):
        for line in self:
            if line.reservation_id and line.partner_id:
                line.reservation_id.partner_id = line.partner_id

    # is_dummy = fields.Boolean(string='Is Dummy Line', default=False)


    # @api.onchange('room_id', 'checkin_date', 'checkout_date')
    # def _onchange_room_conflict(self):
    #     if not self.room_id or not self.checkin_date or not self.checkout_date:
    #         return
    #
    #     overlapping_lines = self.env['hotel.reservation.line'].search([
    #         ('room_id', '=', self.room_id.id),
    #         ('reservation_id.status', '=', 'confirmed'),
    #         ('checkin_date', '<', self.checkout_date),
    #         ('checkout_date', '>', self.checkin_date),
    #         ('id', '!=', self.id),
    #     ])
    #
    #     if overlapping_lines:
    #         self.room_id = False  # Optional: reset room to force correction
    #         raise UserError(_(
    #             "Room '%s' is already reserved from %s to %s.\nPlease choose another room or date."
    #         ) % (
    #                             overlapping_lines[0].room_id.name,
    #                             overlapping_lines[0].checkin_date.strftime('%Y-%m-%d %H:%M'),
    #                             overlapping_lines[0].checkout_date.strftime('%Y-%m-%d %H:%M')
    #                         ))
    #
    #
    @api.onchange('room_id', 'checkin_date', 'checkout_date', 'reservation_id')
    def _check_room_overlap(self):
        for line in self:
            if not line.room_id or not line.checkin_date or not line.checkout_date:
                continue

            overlapping = self.env['hotel.reservation.line'].search([
                ('room_id', '=', line.room_id.id),
                ('reservation_id.status', '=', 'confirmed'),
                ('checkin_date', '<', line.checkout_date),
                ('checkout_date', '>', line.checkin_date),
                ('id', '!=', line.id),
            ])

            if overlapping:
                message = _(
                    "Room '%s' is already reserved from %s to %s in another reservation."
                ) % (
                              line.room_id.name,
                              overlapping[0].checkin_date.strftime('%Y-%m-%d %H:%M'),
                              overlapping[0].checkout_date.strftime('%Y-%m-%d %H:%M')
                          )
                if self.env.context.get('onchange'):
                    raise UserError(message)
                else:
                    raise ValidationError(message)

    # @api.onchange('room_id', 'checkin_date', 'checkout_date', 'reservation_id')
    # def _check_duplicate_room_in_reservation(self):
    #     for line in self:
    #         if not line.room_id or not line.reservation_id:
    #             continue
    #
    #         duplicates = self.env['hotel.reservation.line'].search([
    #             ('room_id', '=', line.room_id.id),
    #             ('id', '!=', line.id),
    #         ])
    #         print(duplicates)
    #
    #         if duplicates:
    #             message = _("Room '%s' is already selected in this reservation.") % line.room_id.name
    #             if self.env.context.get('onchange'):
    #                 raise UserError(message)
    #             else:
    #                 raise ValidationError(message)
    #


    @api.depends('checkin_date', 'checkout_date')
    def _compute_duration(self):
        for line in self:
            if not line.checkin_date or not line.checkout_date:
                line.duration = 1
                continue
            checkin = line.checkin_date
            checkout = line.checkout_date
            if checkout <= checkin:
                line.duration = 1
                continue
            delta = checkout - checkin
            nights = delta.days
            if delta.seconds > 0:
                nights += 1
            line.duration = max(1, nights)

    @api.depends('unit_price', 'checkin_date', 'checkout_date', 'room_taxes_id')
    def _compute_room_price(self):
        for line in self:
            nights = line.duration or 1
            subtotal = line.unit_price * nights
            taxes = line.room_taxes_id.compute_all(
                line.unit_price,
                currency=line.currency_id,
                quantity=nights,
                product=line.room_id,
                partner=line.reservation_id.partner_id
            )
            line.price_total = taxes['total_included'] if taxes else subtotal

    @api.onchange('room_id')
    def onchange_room(self):
        if self.room_id:
            self.unit_price = self.room_id.list_price or 0.0

    # @api.depends('reservation_id.name')
    # def _compute_name(self):
    #     for rec in self:
    #         rec.name = rec.reservation_id.name or 'Reservation'




# ///////////////For Gantt//////////////////////////////

    @api.depends('reservation_id.name', 'reservation_id.partner_id.name')
    def _compute_name(self):
        for rec in self:
            reservation = rec.reservation_id
            customer_name = reservation.partner_id.name or "Unknown Customer"
            reservation_name = reservation.name or "Reservation"
            rec.name = f"{reservation_name} - {customer_name}"


    #  This method works

    # @api.model_create_multi
    # def create(self, vals_list):
    #     Reservation = self.env['hotel.reservation']
    #     # Prepare new vals list with reservation_id ensured
    #     new_vals_list = []
    #     for vals in vals_list:
    #         if not vals.get('reservation_id'):
    #             # Create a new reservation record
    #             reservation_vals = {
    #                 'partner_id': self.env.ref('base.res_partner_1').id,  # default partner, customize if needed
    #                 'status': 'draft',
    #                 'reservation_date': fields.Date.context_today(self),
    #                 'name': Reservation.env['ir.sequence'].next_by_code('hotel.reservation') or 'New',
    #             }
    #             new_reservation = Reservation.create(reservation_vals)
    #             vals['reservation_id'] = new_reservation.id
    #         new_vals_list.append(vals)
    #     # Call super once with full list
    #     return super().create(new_vals_list)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     Reservation = self.env['hotel.reservation']
    #     new_vals_list = []
    #     for vals in vals_list:
    #         if not vals.get('reservation_id'):
    #             reservation_vals = {
    #                 'partner_id': self.env.ref('base.res_partner_1').id,
    #                 'status': 'draft',
    #                 'reservation_date': fields.Date.context_today(self),
    #                 'name': Reservation.env['ir.sequence'].next_by_code('hotel.reservation') or 'New',
    #             }
    #             new_reservation = Reservation.create(reservation_vals)
    #             vals['reservation_id'] = new_reservation.id
    #
    #         # Default partner_id on line to reservation's partner_id
    #         if 'partner_id' not in vals and vals.get('reservation_id'):
    #             reservation = Reservation.browse(vals['reservation_id'])
    #             vals['partner_id'] = reservation.partner_id.id
    #
    #         new_vals_list.append(vals)
    #     return super().create(new_vals_list)

    @api.model_create_multi
    def create(self, vals_list):
        Reservation = self.env['hotel.reservation']
        for vals in vals_list:
            # If reservation_id is missing, create a new one
            if not vals.get('reservation_id'):
                # Get partner_id from line or fallback to a default (optional)
                partner_id = vals.get('partner_id')
                if not partner_id:
                    raise ValueError("Partner is required to create a reservation.")

                # Create the reservation using partner_id from the line
                reservation_vals = {
                    'partner_id': partner_id,
                    'status': 'draft',
                    'reservation_date': fields.Date.context_today(self),
                    'name': Reservation.env['ir.sequence'].next_by_code('hotel.reservation') or 'New',
                }
                reservation = Reservation.create(reservation_vals)
                vals['reservation_id'] = reservation.id

        return super().create(vals_list)


    # //////////////////////////////////// Color Gantt /////////////////////////////////////////////////
    reservation_status = fields.Selection(
        related='reservation_id.status',
        string='Reservation Status',
        readonly=True,
        store=True,
    )

    gantt_color = fields.Integer(string='Gantt Color', compute='_compute_gantt_color')

    @api.depends('reservation_status')
    def _compute_gantt_color(self):
        color_map = {
            'draft': 2,  # blue
            'confirmed': 7,  # green
            'invoiced': 10,  # orange
            'cancelled': 1,  # red
        }
        for rec in self:
            rec.gantt_color = color_map.get(rec.reservation_status, 0)

# ???????????????????????????????????????? Tax for report
    price_tax = fields.Float(string='Tax Amount', compute='_compute_room_tax', store=True)

    @api.depends('unit_price', 'duration', 'room_taxes_id', 'reservation_id.partner_id')
    def _compute_room_tax(self):
        for line in self:
            nights = line.duration or 1
            taxes = line.room_taxes_id.compute_all(
                line.unit_price,
                currency=line.currency_id,
                quantity=nights,
                product=line.room_id,
                partner=line.reservation_id.partner_id,
            )
            line.price_tax = taxes['total_included'] - taxes['total_excluded'] if taxes else 0.0