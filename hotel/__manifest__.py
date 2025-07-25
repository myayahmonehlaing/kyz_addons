# -*- coding: utf-8 -*-
{
    'name': "Hotel",

    'summary': "Odoo 18 Hotel Management Application",

    'description': """
Reservation, Invoiving & Payment, Rooms, Amenities, Services    """,

    'author': "Kaung Yarzar",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'images': ['static/description/icon.png'],

    'depends': ['base', 'account', 'sale_management', 'mail'],




    'data': [

        # "views/reservation_grid_view.xml",


        #security
        'security/ir.model.access.csv',
        'security/security.xml',

        #menu
        'views/hotel_dashboard_views.xml',
        'views/hotel_invoicing_views.xml',
        'views/room_configuration_views.xml',
        'views/hotel_reporting_views.xml',

        'views/hotel_service_views.xml',



        'views/hotel_reservation_views.xml',
        'views/sequence_data.xml',
        'views/hotel_menus.xml',

        'report/report_hotel_reservation.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}
