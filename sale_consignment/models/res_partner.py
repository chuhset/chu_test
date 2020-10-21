# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    consignee = fields.Boolean('Consignee', default=False)
    location_id = fields.Many2one('stock.location',
                                  string='Consignment Location',
                                  readonly=True, )

    def toggle_consignee(self):
        """ Inverse the value of the field ``consignee`` on the records in ``self``. """
        for record in self:
            record.consignee = not record.consignee

            if record.consignee:

                consignment_warehouse = self.env['stock.warehouse']._get_main_consignment_warehouse()

                if record.vat:
                    location_name = record.vat + '/' + record.name
                else:
                    location_name = record.name

                location_value = {'name': location_name,
                                  'usage': 'internal',
                                  'location_id': consignment_warehouse.lot_stock_id.id,
                                  'company_id': self.env.user.company_id.id,
                                  }

                location = self.env['stock.location'].sudo().create(location_value)

                record.sudo().write({'location_id': location.id})

            else:

                record.location_id.sudo().unlink()
