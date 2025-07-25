# my_module/models/sale_order.py
from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='sale_order_id',
        string='Payments',
        readonly=True
    )

    amount_paid = fields.Monetary(
        string='Amount Paid',
        compute='_compute_payment_amounts',
        store=True,
        readonly=True
    )
    amount_due = fields.Monetary(
        string='Amount Due',
        compute='_compute_payment_amounts',
        store=True,
        readonly=True
    )

    payment_count = fields.Integer(
        string='Payment Count',
        compute='_compute_payment_count',
        readonly=True,
    )



    @api.depends('payment_ids.state', 'payment_ids.amount', 'amount_total')
    def _compute_payment_amounts(self):
        """Compute the paid and due amounts for the sales order."""
        for order in self:
            paid_amount = sum(
                order.payment_ids.filtered(lambda p: p.state == 'posted').mapped('amount')
            )
            order.amount_paid = paid_amount
            order.amount_due = order.amount_total - paid_amount

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        """Compute the number of payments related to this sales order."""
        for order in self:
            order.payment_count = len(order.payment_ids)

    def action_open_payment_wizard(self):
        """Open the payment registration wizard for the sales order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Payment'),
            'res_model': 'sale.order.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'sale.order',
                'active_id': self.id,
            },
        }

    def action_register_payment(self, ctx=None):
        """
        Open the sale.order.payment.register wizard to pay the selected sales order.
        This method is kept for compatibility but action_open_payment_wizard is preferred for single orders.
        """
        context = {
            'active_model': 'sale.order',
            'active_ids': self.ids,
        }
        if ctx:
            context.update(ctx)
        return {
            'name': _('Register Payment'),
            'res_model': 'sale.order.payment.register',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_view_payments(self):
        """Open the list of payments related to this sale order."""
        self.ensure_one()

        if not self.payment_ids:
            return self.action_register_payment()

        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments')
        action.update({
            'domain': [('id', 'in', self.payment_ids.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_sale_order_id': self.id,
            },
            'name': _('Payments for %s') % self.name,
        })
        return action

    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     """
    #     Override to find and reconcile prepayments with newly created invoices.
    #     """
    #     invoices = super()._create_invoices(grouped=grouped, final=final, date=date)
    #
    #     # Do not try to reconcile down payment invoices, as they are the prepayment.
    #     if not invoices or self.env.context.get('create_down_payment'):
    #         return invoices
    #
    #     for order in self:
    #         # Find posted, unreconciled payments for this order
    #         payments = order.payment_ids.filtered(
    #             lambda p: p.state == 'posted' and not p.is_reconciled
    #         )
    #         if not payments:
    #             continue
    #
    #         # Get receivable lines from the payments
    #         payment_lines = payments.line_ids.filtered(
    #             lambda line: not line.reconciled and line.account_id.account_type == 'asset_receivable'
    #         )
    #         if not payment_lines:
    #             continue
    #
    #         # Find invoices that were just created from this SO and are posted
    #         order_invoices = invoices.filtered(
    #             lambda inv: inv.state == 'posted' and order.name in inv.invoice_origin.split(', ')
    #         )
    #
    #         for invoice in order_invoices:
    #             # Get receivable lines from the invoice
    #             invoice_lines = invoice.line_ids.filtered(
    #                 lambda line: not line.reconciled and line.account_id.account_type == 'asset_receivable'
    #             )
    #
    #             # Combine lines from the same partner and reconcile them
    #             lines_to_reconcile = (payment_lines + invoice_lines).filtered(
    #                 lambda l: l.partner_id.commercial_partner_id == invoice.commercial_partner_id
    #             )
    #
    #             if lines_to_reconcile:
    #                 lines_to_reconcile.reconcile()
    #
    #     return invoices