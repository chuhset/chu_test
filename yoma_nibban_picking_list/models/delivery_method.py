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

from odoo import models, fields, api, _


class CustomDeliveryMethod(models.Model):
    _name = "custom.delivery.method"
    _description = "Custom Delivery Method"

    name = fields.Char(string="Delivery Method")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_id = fields.Many2one('custom.delivery.method', string="Delivery Method")

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            rec.picking_ids.write({'delivery_id': rec.delivery_id.id})
        return res


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_id = fields.Many2one('custom.delivery.method', string="Delivery Method")