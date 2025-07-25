
{
    'name': "Sale Order Payment Before Opening Invoice",
    'summary': "assign  tasks given by AMA",
    'description': """
    Made the payment first, open invoice later
    """,

    'author': "kyz",
    'website': "https://www.kyz.com",
    'version': '0.1',
    'category': 'Sales',

    'depends': ['base', 'sale',  ],

    'data': [
        'views/account_move_view.xml',
        'views/sale_order_view.xml',
        'security/ir.model.access.csv',
        # 'wizard/sale_order_payment_register_views.xml'
    ],

    'installable' : True,
    'license': 'LGPL-3',
}
