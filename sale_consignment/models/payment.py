# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    consignment_order_ids = fields.Many2many(
        comodel_name='consignment.order',
        relation='consignment_order_transaction_rel',
        column1='transaction_id',
        column2='consignment_order_id',
        string='Transactions', copy=False, readonly=True)