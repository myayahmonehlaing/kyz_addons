from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    template_id = fields.Many2one(
        'sale.order.type.template',
        string='Configuration Template',
        readonly=True,
        check_company=True,
        default=lambda self: self.env.company.template_id.id

    )


    sequence_id = fields.Many2one('ir.sequence', related='template_id.sequence_id', string='Template Sequence', )
    warehouse_id = fields.Many2one('stock.warehouse', related='template_id.warehouse_id', string='Template Warehouse', )
    journal_id = fields.Many2one('account.journal', related='template_id.journal_id', string='Template Journal', )

    name = fields.Char(
        string="Order Reference",
        required=True, copy=False, readonly=False, store=True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _("New")) == _("New"):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date_order'])
                ) if 'date_order' in vals else None

                # Get the raw ID of the custom sequence
                template_id = vals.get('template_id')
                print(f"DEBUG - template_id: {template_id}")
                sequence_id = None
                if template_id:
                    template = self.env['sale.order.type.template'].browse(vals['template_id'])
                    sequence_id = template.sequence_id.id
                    sequence = self.env['ir.sequence'].browse(sequence_id)  # Now it's a record
                    print(f"DEBUG - sequence_id: {sequence_id}")
                    print(f"DEBUG - sequence: {sequence}")

                    sequence = self.env['ir.sequence'].browse(sequence_id)
                    # company_id = vals.get('company_id') or self.env.company.id
                    vals['name'] = sequence.with_company(vals.get('company_id')).next_by_id(
                        sequence_date=seq_date) or _("New")

                else:
                    vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(
                        'sale.order', sequence_date=seq_date) or _("New")

        return super().create(vals_list)


    def action_confirm(self):
        res = super().action_confirm()

        config_param = self.env['ir.config_parameter'].sudo()
        auto_invoice = config_param.get_param('sale_order_type.auto_invoice') == 'True'
        auto_picking_done = config_param.get_param('sale_order_type.auto_picking_done') == 'True'

        # Auto-create and post invoice
        for order in self:
            if auto_invoice:
                invoices = order._create_invoices()
                for invoice in invoices:
                    invoice.action_post()

        # Auto-validate delivery (picking)
        for order in self:
            if auto_picking_done:
                for picking in order.picking_ids:
                    if picking.picking_type_code != 'outgoing':
                        continue
                    if picking.state in ('done', 'cancel'):
                        continue

                    if picking.state == 'draft':
                        picking.action_confirm()
                    if picking.state in ('confirmed', 'waiting'):
                        picking.action_assign()
                    if picking.state == 'assigned':
                        for move in picking.move_ids_without_package:
                            for move_line in move.move_line_ids:
                                if move_line.qty_done == 0:
                                    move_line.qty_done = move.product_uom_qty
                        picking.button_validate()

        return res
