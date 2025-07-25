
from odoo import models, fields, api


# The main model for our curated hotel services
class HotelService(models.Model):
    _name = 'hotel.service'
    _description = 'Hotel Service'
    _inherits = {'product.product': 'product_id'}


    name = fields.Char(
        related='product_id.name',
        readonly=False,
        string='Name',
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product Service',
        required=True,
        ondelete='cascade',
        auto_join=True,
        help="The product related to this service for sales and invoicing."
    )

    taxes_id = fields.Many2many(
        'account.tax',
        related='product_id.taxes_id',
        string="Taxes",
        readonly=False,
        check_company=True
    )
    service_type_id = fields.Many2one('hotel.service.type', string='Service Categories', required=True)

    description = fields.Text(string='Description')
    list_price = fields.Float(string='Price')

    type = fields.Selection(related='product_id.type', readonly=False, string='Good or Service', required=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Helper to prepare values for the underlying product
    def _prepare_product_vals(self, service_vals):
        """Prepare values for the product.product record."""
        return {
            'name': service_vals.get('name'),
            'type': service_vals.get('type'),  # Default to 'service'
            'list_price': service_vals.get('list_price'),
            'invoice_policy': 'order',
            'categ_id': self.env.ref('product.product_category_all').id,
            'description': service_vals.get('description'),
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to automatically generate the underlying product.product
        if it's not already provided.
        """
        Product = self.env['product.product']
        for vals in vals_list:
            # If a product_id is not specified, create one.
            if not vals.get('product_id'):
                product_vals = self._prepare_product_vals(vals)
                new_product = Product.create(product_vals)
                vals['product_id'] = new_product.id
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write to ensure that changes to key fields on the hotel.service
        form are also written to the underlying product.product record. This is
        essential for keeping data consistent for invoicing.
        """
        # First, call the original write to update the hotel.service record
        res = super().write(vals)

        # Identify fields that need to be synchronized with the product model
        product_fields_to_sync = ['name', 'list_price', 'description', 'type']

        # Prepare a dictionary of values to update on the product
        product_vals_to_update = {}
        for field in product_fields_to_sync:
            if field in vals:
                product_vals_to_update[field] = vals[field]

        # If there are values to update, write them to the related product record(s)
        if product_vals_to_update:
            # self.mapped('product_id') ensures this works for multiple records at once
            self.mapped('product_id').write(product_vals_to_update)

        return res
