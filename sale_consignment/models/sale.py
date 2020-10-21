# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id.consignee:

            consignment_warehouse = self.env['stock.warehouse']._get_main_consignment_warehouse()
            self.warehouse_id = consignment_warehouse.id

        else:
            self.warehouse_id = self._default_warehouse_id()

    def _action_confirm(self):
        super(SaleOrder, self)._action_confirm()
        for order in self:
            if order.partner_id.consignee and order.warehouse_id.code =='CO.WH':
                location_src = order.partner_id.location_id
                for picking in order.picking_ids:
                    picking.sudo().write({'location_id':location_src.id})
                    for move in picking.move_lines:
                        for move_line in move.move_line_ids:
                            move_line.sudo().write({'location_id':location_src.id})
