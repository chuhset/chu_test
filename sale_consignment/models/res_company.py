# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    used_consignment = fields.Boolean(default=False, string="Use Consignment")

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)

        self.env['stock.warehouse'].sudo().create({
            'name': 'Consignment Warehouse',
            'code': 'CO.WH',
            'company_id': company.id,
            'consignment_source': True,
            'partner_id': company.partner_id.id})

        return company

    def write(self, values):

        if 'used_consignment' in values:

            if values.get("used_consignment"):

                warehouses = self.env['stock.warehouse'].search(
                    [('company_id', '=', self.id), ('code', '=', "CO.WH")])

                if not warehouses.exists():
                    self.env['stock.warehouse'].sudo().create({
                        'name': 'Consignment Warehouse',
                        'code': 'CO.WH',
                        'company_id': self.id,
                        'consignment_source': True,
                        'partner_id': self.partner_id.id})

        return super(Company, self).write(values)
