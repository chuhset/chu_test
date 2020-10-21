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

from  odoo import models, fields, api


class InventoryIssueNotes(models.AbstractModel):
    _name = 'report.yoma_nibban_picking_list.report_issue_notes_temp'
    _description = 'Report for Picking List'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('yoma_nibban_picking_list.report_issue_notes_temp')
        return {
                'doc_ids': self.env['order.report.issue.notes.ee'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self,
                'data': data,
                'get_inventory_details': self.get_inventory_details,
                   }


    def get_inventory_details(self,obj):

        stock_picking_ids = self.env['stock.picking'].sudo().search([])

        stock_picking=[]
        for stock_picking_id in stock_picking_ids:
            if stock_picking_id.location_id.id == obj.location_id.id and stock_picking_id.state == 'assigned' and stock_picking_id.scheduled_date.date() == obj.scheduled_date:
                for carrier in obj.carrier_ids:
                    if stock_picking_id.delivery_id.id == carrier.id:
                          stock_picking.append(stock_picking_id.id)

        product_details = []
        for stock in stock_picking:
            stock_picking_rec = self.env['stock.picking'].sudo().browse(stock)
            if stock_picking_rec.picking_type_id.code in ['outgoing','internal']:
                for line in stock_picking_rec.move_ids_without_package:
                    product_details.append({
                        'id': line.product_id.id,
                        'unit': line.product_uom.name,
                        'qty': line.product_uom_qty,
                        'carrier':stock_picking_rec.delivery_id.id,
                    })


        custom_list = []
        for each_prod in product_details:
            if each_prod.get('id') not in [x.get('id') for x in custom_list] or each_prod.get('carrier') not in [
                y.get('carrier') for y in custom_list]:
                custom_list.append(each_prod)
            else:
                count = 0
                for each in custom_list:
                    if each.get('id') == each_prod.get('id') and each.get('carrier') == each_prod.get('carrier'):
                        each.update({'qty': each.get('qty') + each_prod.get('qty')})
                        count = count + 1

                if count == 0:
                    custom_list.append(each_prod)

        final_dict = {}
        for key in custom_list:
            if key['carrier'] not in final_dict:
                final_dict.update({key['carrier']: [key]})
            else:
                final_dict[key['carrier']] += [key]

        return final_dict
