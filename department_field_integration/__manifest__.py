
{
    'name': "Department Field Integration and Record Rules",
    'summary': "Department Field Added to Sale ROQ and Account Invoice and connected with Department from HR",
    'description': """
    
- Department field added in sale module
- Department filed added in accounting module


 ### This module a collection assign tasks given by AMA
    """,

    'author': "kaung yarzar",
    'website': "",
    'version': '0.1',
    'category': 'Uncategorized',


    'depends': ['base', 'sale', 'hr','sales_team', 'account', 'accountant'],

    'data': [
        'data/app_category.xml', #adding a new custom category
        'security/ir.model.access.csv',
        'views/view_changes.xml',
        # 'security/security.xml',
    ],

    'installable' : True,
    'license': 'LGPL-3',
}
