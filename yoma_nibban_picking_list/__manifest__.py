# -*- coding: utf-8 -*-
#################################################################################
# Author : Yoma Technologies Co. Ltd. (<https://www.yomatechnologies.com>)
# Copyright(c): 2012-Present Yoma Technologies Co. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'yoma_nibban_picking_list',
    'category': 'Inventory',
    'author': 'Yoma Technologies Co. Ltd.',
    'website': 'https://www.yomatechnologies.com',
    'summary': '''Allows user to add custom delivery method into sale and inventory, User can print picking list report in PDF.''',
    'description': '''Allows user to add custom delivery method into sale and inventory, User can print picking list report in PDF.''',
    'depends': ['base', 'sale_management','stock','delivery','sale_consignment'],
    'data': ['security/ir.model.access.csv',
             'views/delivery_method_view.xml',
             'views/issue_notes_report_temp_view.xml',
             'views/report.xml',
             'views/product_delivery_report_view.xml',
             'views/delivery_method_consignment_form_view.xml',
            ],
    'demo': ['data/delivery_method_demo.xml'],
    'images': [],
    'installable': True,
    'auto_install': False,
}

