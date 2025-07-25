
{
    'name': "Sale Order Type Template Configuration",
    'summary': "assign tasks given by AMA",
    'description': """
    Made a sale order type template in setting sales,
    added a template field in RFQ,
    Added Auto Delivery Setting,
    Added Auto Invoice Setting,
    """,

    'author': "Kaung Yarzar",
    'website': "https://www.kyz.com",
    'version': '0.1',
    'category': 'Sales',

    'depends': ['account', 'hr', 'sale', 'sales_team', 'stock',],

    'data': [
        'security/ir.model.access.csv',
        'views/setting_view.xml',
        'views/sale_order_view_inherit.xml',
        'views/sale_menus_inherit.xml',
    ],

    'installable' : True,
    'license': 'LGPL-3',
}
