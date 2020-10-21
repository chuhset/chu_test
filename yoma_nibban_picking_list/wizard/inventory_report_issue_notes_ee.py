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
from  odoo import models, fields, api, _

class inventory_report_issue_notes_ee(models.TransientModel):
    _name = 'order.report.issue.notes.ee'
    _description = 'Issue Notes Report'

    scheduled_date = fields.Date(string="Scheduled Date",required=True)
    location_id = fields.Many2one('stock.location', "From Location",required=True)
    carrier_ids = fields.Many2many("custom.delivery.method", string="Delivery Methods")


    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        data = self.env.context.get('active_ids', [])
        datas = {
            'ids': self.ids,
            'model': 'order.report.issue.notes.ee',
            'form': data
        }
        return self.env.ref('yoma_nibban_picking_list.action_report_by_issue_notes').report_action(self, data=datas)

