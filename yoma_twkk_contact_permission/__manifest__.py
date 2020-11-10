# -*- coding: utf-8 -*-
{
    'name': "Yoma TWKK Contact Permission",
    'version': '1.0',
    'author': "Yoma Technologies",
    'category': 'Customisation',
    'summary' :"""(1) We need to click Hide Create Button On Contact in user template form. (need to activate developer mode)
                      (2) When the user that is restricted logins in, she cannot see create button in Contact View(form,tree,kaban)""",
    'website': 'http://www.yomatechnologies.com/',
    'depends': [
        'purchase','base',
    ],

    'data': [
        'security/custom_hide_cost_security.xml'
    ],

    'qweb': [

    ],

    'img': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
