from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'



    template_id = fields.Many2one(
        'sale.order.type.template',
        related='company_id.template_id',
        string='Configuration Template',
        ondelete='set null',
        readonly=False,
        store=True,
        check_company=True,

    )



    # These fields will be automatically filled from the template
    name = fields.Char(related='company_id.template_id.name', required=True)
    sequence_id = fields.Many2one(related='company_id.template_id.sequence_id', readonly=False)
    warehouse_id = fields.Many2one(related='company_id.template_id.warehouse_id', readonly=False)
    journal_id = fields.Many2one(related='company_id.template_id.journal_id', readonly=False)
    auto_invoice = fields.Boolean( readonly=False)
    auto_picking_done = fields.Boolean(readonly=False)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.name = self.template_id.name
            self.sequence_id = self.template_id.sequence_id
            self.warehouse_id = self.template_id.warehouse_id
            self.journal_id = self.template_id.journal_id

    def set_values(self):
        super().set_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        # IrConfigParam.set_param('sale_order_type.template_id', self.template_id.id or False)
        IrConfigParam.set_param('sale_order_type.auto_invoice', self.auto_invoice)
        IrConfigParam.set_param('sale_order_type.auto_picking_done', self.auto_picking_done)


    # def get_values(self):
    #     res = super().get_values()
    #     IrConfigParam = self.env['ir.config_parameter'].sudo()
    #     res.update({
    #         # 'template_id': int(IrConfigParam.get_param('sale_order_type.template_id', default=0)) or False,
    #         'auto_invoice': IrConfigParam.get_param('sale_order_type.auto_invoice') == 'True',
    #         'auto_picking_done': IrConfigParam.get_param('sale_order_type.auto_picking_done') == 'True',
    #     })
    #     return res



    def get_values(self):
        res = super().get_values()
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # By providing a default value, we ensure get_param always returns a string.
        # This is more explicit and safer than relying on it returning a boolean False.
        res.update({
            'auto_invoice': IrConfigParam.get_param('sale_order_type.auto_invoice', default='False') == 'True',
            'auto_picking_done': IrConfigParam.get_param('sale_order_type.auto_picking_done', default='False') == 'True',
        })
        return res
