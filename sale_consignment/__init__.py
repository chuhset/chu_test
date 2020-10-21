# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID


def _create_consignment_rules(cr, registry):
    """ This hook is used to add a default consignment_rule_id on every warehouse. It is
    necessary if the sale_consignment module is installed after some warehouses
    were already created.
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    company_ids = env['res.company'].search([('used_consignment', '=', False)])

    for company_id in company_ids:

        company_id.sudo().write({'used_consignment': True})

    warehouse_ids = env['stock.warehouse'].search([('consignment_rule_id', '=', False)])

    for warehouse_id in warehouse_ids:

        warehouse_id.write({'consignment_source': True})