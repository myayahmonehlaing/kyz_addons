
{
    'name': "Fix Price Discount In Sale Order Form",
    'summary': "assign tasks given by AMA",
    'description': """
    Fixed discount field in sale order form and invoice form
    """,

    'author': "kaung Yarzar",
    'version': '0.1',
    'category': 'Sales',

    'depends': ['base', 'sale',  ],

    'data': [
        # 'views/sale_order_line_views_inherit.xml',
        'views/sale_order_views_inherit.xml',
        'views/account_move_views_inherit.xml',
        'report/report_saleorder_document.xml',
        'report/report_invoice_document.xml',

    ],

    'installable' : True,
    'license': 'LGPL-3',
}
