# my_module/models/account_move.py
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # This field links an invoice back to its source Sale Order.
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Sale Order',
        index=True,
        copy=False,
        help="Link to the Sale Order that originated this invoice or payment."
    )

    matched_payment_ids = fields.Many2many(
        string="Matched Payments",
        comodel_name='account.payment',
        copy=False,
    )


    sale_order_payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='sale_order_id',
        compute='_compute_sale_order_payments',
        string='Sale Order Payments',
        store=False,
    )
    sale_order_payment_count = fields.Integer(
        string='Sale Order Payment Count',
        compute='_compute_sale_order_payments',
        store=False,
    )



    def action_post(self):
        """
        Extend the posting process to automatically reconcile a new invoice
        with any outstanding partner credits (like prepayments).
        """
        # Call the original action_post. It returns True on success or a dict for an action.
        res = super().action_post()

        # If the super method returned a wizard (e.g., for bank matching), don't interfere.
        if isinstance(res, dict):
            return res


        for move in self.filtered(lambda m: m.is_invoice(include_receipts=True) and m.state == 'posted'):
            # Partner's receivable or payable account.
            partner = move.commercial_partner_id
            account = (
                partner.property_account_receivable_id
                if move.is_sale_document(include_receipts=True)
                else partner.property_account_payable_id
            )
            if not account:
                continue

            # For a customer invoice, we look for existing credits (prepayments).
            # For a vendor bill, we look for existing debits (prepayments).
            credit_or_debit_field = 'credit' if move.is_sale_document(include_receipts=True) else 'debit'


            # Find all posted, unreconciled payment/credit lines for this partner.
            payment_lines = self.env['account.move.line'].search([
                ('company_id', '=', move.company_id.id),
                ('account_id', '=', account.id),
                ('partner_id', '=', partner.id),
                ('reconciled', '=', False),
                (credit_or_debit_field, '>', 0),
                ('move_id.state', '=', 'posted'),
            ])

            if not payment_lines:
                continue

            # Find the receivable/payable line from the current invoice.
            invoice_line = move.line_ids.filtered(
                lambda line: line.account_id == account and not line.reconciled
            )

            # If both the invoice and payments are found, reconcile them.
            if invoice_line:
                lines_to_reconcile = payment_lines + invoice_line
                try:
                    lines_to_reconcile.reconcile()
                    _logger.info("Successfully reconciled invoice %s with outstanding payments/credits.", move.name)
                except Exception as e:
                    _logger.error("Failed to automatically reconcile invoice %s. Error: %s", move.name, e)

        return res



    @api.depends('invoice_origin')
    def _compute_sale_order_payments(self):
        for move in self:
            payments = self.env['account.payment'].search([
                ('sale_order_id.name', '=', move.invoice_origin)
            ])
            move.sale_order_payment_ids = payments
            move.sale_order_payment_count = len(payments)

    def action_view_sale_order_payments(self):
        self.ensure_one()
        payments = self.sale_order_payment_ids
        if not payments:
            return {'type': 'ir.actions.act_window_close'}
        elif len(payments) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Sale Order Payment'),
                'view_mode': 'form',
                'res_model': 'account.payment',
                'res_id': payments.id,
                'target': 'current',
            }