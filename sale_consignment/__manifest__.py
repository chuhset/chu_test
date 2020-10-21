# -*- coding: utf-8 -*-

{
    'name': 'Yoma Sale Consignment',
    'version': '2.0',
    'category': 'Sales',
    'summary': 'Sales Consignment',
    'description': """
Sales Consignment.
    """,
    'depends': ['sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/consignment_views.xml',
        'views/consignee_views.xml',
        'views/stock_warehouse_views.xml',
        'views/res_company_views.xml',
        'data/ir_sequence_data.xml',
        'data/stock_data.xml',
        'report/consignment_report.xml',
        'report/consignment_report_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': '_create_consignment_rules',
}
