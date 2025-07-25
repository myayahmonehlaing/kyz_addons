
{
    'name': "Record Rules for Accounting and Sales",
    'summary': "assign tasks given by AMA",
    'description': """
- Record Rules written for Sale Module ( Department: Document Only )
- Record Rules written for Account Module ( Department Only )
    """,

    'author': "kaung yarzar",
    'website': "https://www.kyz.com",
    'version': '0.1',
    'category': 'Uncategorized',

    'depends': ['base','account','accountant', 'hr', 'sale', 'sales_team', ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/invoice_department_group_view.xml',

    ],

    'installable' : True,
    'license': 'LGPL-3',
}
