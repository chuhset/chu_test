# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    consignment_source = fields.Boolean('Consignment Source',
                                 default=False,
                                 help="When products are out for consignment, they can be take out from this warehouse.")

    consignment_rule_id = fields.Many2one('stock.rule', 'Consignment rule')

    consignment_type_id = fields.Many2one('stock.picking.type', 'Consignment Type')

    def get_rules_dict(self):
        result = super(StockWarehouse, self).get_rules_dict()

        for warehouse in self:
            result[warehouse.id]['consignment'] = [
                self.Routing(warehouse.lot_stock_id, warehouse.lot_stock_id, warehouse.consignment_type_id, 'pull')]
        return result

    def _get_sequence_values(self):

        sequence_values = super(StockWarehouse, self)._get_sequence_values()

        sequence_values['consignment_type_id'] = {
            'name': self.name + ' ' + _('Sequence consignment'),
            'prefix': self.code + '/CON/', 'padding': 5,
            'company_id': self.company_id.id,
        }

        return sequence_values

    def _get_picking_type_create_values(self, max_sequence):

        picking_type_create_values, max_sequence = super(StockWarehouse, self)._get_picking_type_create_values(
            max_sequence)

        picking_type_create_values['consignment_type_id'] = {
            'name': _('Consignment Transfer'),
            'code': 'internal',
            'use_create_lots': True,
            'use_existing_lots': False,
            'default_location_src_id': self.lot_stock_id.id,
            'default_location_dest_id': self.lot_stock_id.id,
            'sequence': max_sequence,
            'sequence_code': 'CON',
            'company_id': self.company_id.id,
        }

        return picking_type_create_values, max_sequence + 1

    def _get_picking_type_update_values(self):

        picking_type_update_values = super(StockWarehouse, self)._get_picking_type_update_values()

        picking_type_update_values['consignment_type_id'] = {}

        return picking_type_update_values

    def _get_global_route_rules_values(self):

        global_route_rules_values = super(StockWarehouse, self)._get_global_route_rules_values()

        rule = self.get_rules_dict()[self.id]['consignment']
        rule = [r for r in rule if r.from_loc == self.lot_stock_id][0]
        location_id = rule.from_loc
        location_dest_id = rule.dest_loc
        picking_type_id = rule.picking_type

        global_route_rules_values['consignment_rule_id'] = {
            'depends': [],
            'create_values': {
                'active': True,
                'company_id': self.company_id.id,
                'action': 'pull',
                'auto': 'manual',
                'route_id': self._find_global_route('sale_consignment.route_warehouse_consignment', _('Consignment')).id
            },
            'update_values': {
                'name': self._format_rulename(location_id, location_id, 'Consignment'),
                'location_id': location_dest_id.id,
                'location_src_id': location_id.id,
                'picking_type_id': picking_type_id.id,
            }
        }

        return global_route_rules_values

    def _get_main_consignment_warehouse(self):

        return self.search([('company_id', '=', self.env.user.company_id.id), ('code', '=', "CO.WH")], limit=1)

    def _get_all_routes(self):
        routes = super(StockWarehouse, self).get_all_routes_for_wh()
        routes |= self.filtered(
            lambda self: self.consignment_source and self.consignment_rule_id and self.consignment_rule_id.route_id).mapped(
            'consignment_rule_id').mapped('route_id')
        return routes

    def _update_name_and_code(self, name=False, code=False):
        res = super(StockWarehouse, self)._update_name_and_code(name, code)
        warehouse = self[0]

        if warehouse.consignment_rule_id and name:
            warehouse.consignment_rule_id.sudo().write(
                {'name': warehouse.consignment_rule_id.name.replace(warehouse.name, name, 1)})

        return res

    def write(self, vals):

        if 'consignment_source' in vals:
            if vals.get("consignment_source"):
                for warehouse in self.filtered(lambda warehouse: not warehouse.consignment_rule_id):
                    # create sequences and operation types
                    new_vals = warehouse._create_or_update_sequences_and_picking_types()
                    warehouse.sudo().write(new_vals)  # TDE FIXME: use super ?
                    # create routes and push/stock rules
                    route_vals = warehouse._create_or_update_route()
                    warehouse.sudo().write(route_vals)

                    # Update global route with specific warehouse rule.
                    warehouse._create_or_update_global_routes_rules()

        return super(StockWarehouse, self).write(vals)


class StockMove(models.Model):
    _inherit = "stock.move"
    consignment_line_id = fields.Many2one('consignment.order.line', 'Consignment Line')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('consignment_line_id')
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.consignment_line_id.id)
        return keys_sorted

    def _action_done(self, cancel_backorder=False):
        result = super(StockMove, self)._action_done(cancel_backorder)
        for line in result.mapped('consignment_line_id').sudo():
            line.qty_delivered = line._get_qty_procurement()
        return result

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'product_uom_qty' in vals:
            for move in self:
                if move.state == 'done':
                    consignment_order_lines = self.filtered(
                        lambda move: move.consignment_line_id and move.product_id.expense_policy == 'no').mapped(
                        'consignment_line_id')
                    for line in consignment_order_lines.sudo():
                        line.qty_delivered = line._get_qty_procurement()
        return res

    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new and self.consignment_line_id and self.consignment_line_id.order_id:
            self.picking_id.message_post_with_view(
                'mail.message_origin_link',
                values={'self': self.picking_id, 'origin': self.consignment_line_id.order_id},
                subtype_id=self.env.ref('mail.mt_note').id)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    consignment_id = fields.Many2one('consignment.order', 'Consignment Order')

    @api.model
    def _get_rule(self, product_id, location_id, values):

        res = self.env['stock.rule']

        if values.get('consignment', False):
            warehouse = values.get('warehouse_id', False)
            res = warehouse.consignment_rule_id
        if not res:
            res = super(ProcurementGroup, self)._get_rule(product_id, location_id, values)

        return res


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        result = super(StockRule, self)._get_stock_move_values(
            product_id=product_id,
            product_qty=product_qty,
            product_uom=product_uom,
            location_id=location_id,
            name=name,
            origin=origin,
            company_id=company_id,
            values=values)

        if values.get('consignment_line_id', False):
            result['consignment_line_id'] = values['consignment_line_id']
        return result


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    consignment_id = fields.Many2one(related="group_id.consignment_id", string="Consignment Order", store=True)
