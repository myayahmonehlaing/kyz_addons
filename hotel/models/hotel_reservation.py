# in models/hotel_reservation.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # --- Core Fields ---
    name = fields.Char(
        string='Reservation ID', required=True, copy=False, readonly=True,
        default=lambda self: _('New'), tracking=True
    )
    reservation_date = fields.Date(string='Reservation Date', default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', copy=False, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')


    service_line_ids = fields.One2many('hotel.reservation.service', 'reservation_id', string='Service Lines')


    room_line_ids = fields.One2many('hotel.reservation.line', 'reservation_id', string='Room Lines')


    # --- Invoicing Fields ---
    invoice_ids = fields.One2many('account.move', 'reservation_id', string='Invoices')
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count', store=True)

    # --- Compute & Onchange Methods ---

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or 'New'
        return super().create(vals_list)


    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for res in self:
            res.invoice_count = len(res.invoice_ids)

    # --- Action Buttons ---

    def action_confirm(self):
        self.write({'status': 'confirmed'})
        # Optional: Set the room state to 'occupied'
        # self.room_id.write({'state': 'occupied'})
        return True

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_count > 0:
            raise UserError(_("An invoice already exists for this reservation."))

        invoice_vals = self._prepare_invoice_values()
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'status': 'invoiced'})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def _prepare_invoice_values(self):
        self.ensure_one()
        invoice_line_ids = []

        # 1. Add Room Lines
        for room_line in self.room_line_ids:
            if room_line.unit_price > 0:
                product = room_line.room_id.product_id
                if not product:
                    raise UserError(_(
                        "No product configured for room '%s'. Please set a product on the room."
                    ) % room_line.room_id.name)

                invoice_line_ids.append((0, 0, {
                    'product_id': product.id,
                    'name': f"From: {room_line.checkin_date.strftime('%Y-%m-%d %H:%M')} To: {room_line.checkout_date.strftime('%Y-%m-%d %H:%M')}",
                    'quantity': room_line.duration,
                    'price_unit': room_line.unit_price,
                    'tax_ids': [(6, 0, room_line.room_taxes_id.ids)],
                }))

        # 2. Add Service Lines
        for service in self.service_line_ids:
            product = service.service_id.product_id
            if not product:
                raise UserError(_(
                    "No product configured for service '%s'. Please set a product on the service."
                ) % service.service_id.name)

            invoice_line_ids.append((0, 0, {
                'product_id': product.id,
                'name': service.service_id.name,
                'quantity': service.quantity,
                'price_unit': service.price_unit,
                'tax_ids': [(6, 0, product.taxes_id.ids)],
            }))

        return {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'reservation_id': self.id,
            'invoice_line_ids': invoice_line_ids,
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('reservation_id', '=', self.id)],
            'context': {'default_move_type': 'out_invoice', 'create': False},
        }

    def action_cancel(self):
        self.write({'status': 'cancelled'})
        # self.room_id.write({'state': 'available'})
        return True

    def action_reset_to_draft(self):
        self.write({'status': 'draft'})
        return True



    room_price = fields.Monetary(
        string='Room Total',
        compute='_compute_total_amounts',
        store=True
    )
    service_total = fields.Monetary(
        string='Service Total',
        compute='_compute_total_amounts',
        store=True
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amounts',
        store=True
    )

    @api.depends('room_line_ids.price_total', 'service_line_ids.subtotal')
    def _compute_total_amounts(self):
        for rec in self:
            room_total = sum(line.price_total for line in rec.room_line_ids)
            service_total = sum(line.subtotal for line in rec.service_line_ids)
            rec.room_price = room_total
            rec.service_total = service_total
            rec.total_amount = room_total + service_total
