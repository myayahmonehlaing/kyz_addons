from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderPaymentRegister(models.TransientModel):
    _name = 'sale.order.payment.register'
    _description = 'Register Prepayment for Sales Order'

    # == Fields for the Wizard ==
    sale_order_id = fields.Many2one('sale.order', string="Sales Order", readonly=True, required=True)
    company_id = fields.Many2one(related='sale_order_id.company_id')
    partner_id = fields.Many2one(related='sale_order_id.partner_id', string="Customer", readonly=True)
    currency_id = fields.Many2one(related='sale_order_id.currency_id', string='Currency', readonly=True)

    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    communication = fields.Char(string="Memo")

    # Fields for Payment Method
    available_payment_method_line_ids = fields.Many2many(
        comodel_name='account.payment.method.line',
        compute='_compute_available_payment_methods',
    )
    payment_method_line_id = fields.Many2one(
        comodel_name='account.payment.method.line',
        string='Payment Method',
        readonly=False,
        store=True,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'sale.order' and self._context.get('active_id'):
            so = self.env['sale.order'].browse(self._context.get('active_id'))
            journal = self.env['account.journal'].search(
                [('company_id', '=', so.company_id.id), ('type', 'in', ('bank', 'cash'))], limit=1)
            res.update({
                'sale_order_id': so.id,
                'amount': so.amount_total,
                'communication': so.name,
                'journal_id': journal.id if journal else False,
            })
        return res

    @api.depends('journal_id')
    def _compute_available_payment_methods(self):
        """Compute the available payment methods based on the journal."""
        for wizard in self:
            if wizard.journal_id:
                # We are receiving money, so payment_type is 'inbound'
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines('inbound')
            else:
                wizard.available_payment_method_line_ids = False

    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        """Compute and select a default payment method."""
        for wizard in self:
            if wizard.payment_method_line_id in wizard.available_payment_method_line_ids:
                # The selected method is still valid, do nothing
                continue
            if wizard.available_payment_method_line_ids:
                # Select the first available one by default
                wizard.payment_method_line_id = wizard.available_payment_method_line_ids[0]._origin
            else:
                wizard.payment_method_line_id = False

    def action_create_payment(self):
        """Create and post the payment."""
        self.ensure_one()

        # Validate before creating payment
        if self.amount <= 0:
            raise UserError(_("The payment amount must be positive."))

        try:
            # Create payment
            payment_vals = self._create_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)

            # Post the payment
            payment.action_post()

            # Add message to sale order
            self.sale_order_id.message_post(
                body=_("A payment of %s %s was created via the prepayment wizard.") % (
                    payment.amount, payment.currency_id.symbol
                )
            )

            # Link the payment to the sale order
            self.sale_order_id.payment_ids = [Command.link(payment.id)]

            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': payment.id,
                'view_mode': 'form',
            }

        except Exception as e:
            raise UserError(_("Error creating payment: %s") % str(e))

    def _create_payment_vals(self):
        """Prepare payment values."""
        self.ensure_one()

        if self.amount <= 0:
            raise UserError(_("The payment amount must be positive."))

        return {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_reference': self.communication or self.sale_order_id.name,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'company_id': self.company_id.id,
            'destination_account_id': self.partner_id.property_account_receivable_id.id,
        }