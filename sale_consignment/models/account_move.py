# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    consignment_order_line_ids = fields.Many2many(
        comodel_name='consignment.order.line',
        relation='consignment_order_line_invoice_rel',
        column1='invoice_line_id',
        column2='consignment_order_line_id',
        string='Sales Order Lines', readonly=True, copy=False)

