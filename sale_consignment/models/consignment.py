# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ConsignmentOrder(models.Model):
    _name = "consignment.order"
    _inherit = 'sale.order'
    _description = "Consignment Order"
    _order = 'date_order desc, id desc'

    def onchange_partner_id(self):
        pass

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search(
            [('company_id', '=', company),
             ('consignment_source', '=', True),
             ('code', '!=', "CO.WH")], limit=1)
        return warehouse_ids

    transaction_ids = fields.Many2many(
        comodel_name='payment.transaction',
        relation='consignment_order_transaction_rel',
        column1='consignment_order_id',
        column2='transaction_id',
        string='Transactions', copy=False, readonly=True)

    warehouse_id = fields.Many2one(
        domain=[
            ('consignment_source', '=', True),
            ('code', '!=', "CO.WH")],
        string="Source Warehouse")

    picking_ids = fields.One2many('stock.picking', 'consignment_id', string='Pickings')

    partner_id = fields.Many2one(
        'res.partner', string='Consignee', readonly=True,
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]},
        required=True,
        change_default=True,
        index=True,
        tracking=1,
        domain="['|', '|', ('company_id', '=', False), ('company_id', '=', company_id), ('consignee','=',True)]", )

    consignment_date = fields.Datetime(string='Consignment Date', required=True, copy=False,
                                       default=fields.Datetime.now)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    order_line = fields.One2many('consignment.order.line', 'order_id')

    @api.model
    def create(self, vals):

        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'consignment.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('consignment.order') or _('New')

        result = super(ConsignmentOrder, self).create(vals)

        return result


class ConsignmentOrderLine(models.Model):
    _name = 'consignment.order.line'
    _inherit = 'sale.order.line'
    _description = 'Consignment Order Line'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('consignment.order')

    move_ids = fields.One2many('stock.move', 'consignment_line_id', string='Stock Moves')

    invoice_lines = fields.Many2many(
        comodel_name='account.move.line',
        relation='consignment_order_line_invoice_rel',
        column1='consignment_order_line_id',
        column2='invoice_line_id',
        string='Invoice Lines', copy=False)

    def action_done(self):
        for order in self:
            tx = order.sudo().transaction_ids.get_last_transaction()
            if tx and tx.state == 'pending' and tx.acquirer_id.provider == 'transfer':
                tx._set_transaction_done()
                tx.write({'is_processed': True})
        return self.write({'state': 'done'})

    def _prepare_procurement_group_vals(self):
        return {
            'name': self.order_id.name,
            'move_type': self.order_id.picking_policy,
            'sale_id': False,
            'consignment_id': self.order_id.id,
            'partner_id': self.order_id.partner_shipping_id.id,
        }

    def _prepare_procurement_values(self, group_id=False):

        values = super(ConsignmentOrderLine, self)._prepare_procurement_values(group_id)

        values.update({
            'sale_line_id': False,
            'consignment_line_id': self.id,
        })
        return values

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)

            values.update({
                'consignment': True,
            })

            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(self.env['procurement.group'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_id.location_id,
                line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        orders = list(set(x.order_id for x in self))
        for order in orders:
            reassign = order.picking_ids.filtered(lambda x: x.state=='confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
            if reassign:
                reassign.action_assign()
        return True

    def _get_qty_procurement(self, previous_product_uom_qty=False):
        self.ensure_one()
        qty = 0.0
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        consignment_warehouse = self.env['stock.warehouse']._get_main_consignment_warehouse()
        consignment_location = consignment_warehouse.lot_stock_id
        for move in outgoing_moves:
            if move.location_dest_id.location_id.id == consignment_location.id:
                qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom,
                                                          rounding_method='HALF-UP')
        for move in incoming_moves:
            if move.location_dest_id.location_id.id != consignment_location.id:
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom,
                                                          rounding_method='HALF-UP')
        return qty

    def _check_routing(self):

        is_available = False
        product_routes = self.route_id or (self.product_id.route_ids + self.product_id.categ_id.total_route_ids)

        # Check Consignment Route
        wh_consignment_route = self.order_id.warehouse_id.consignment_rule_id.route_id
        if wh_consignment_route and wh_consignment_route <= product_routes:
            is_available = True
        else:
            consignment_route = False
            try:
                consignment_route_id = self.env['stock.warehouse']._find_global_route(
                    'sale_consignment.route_warehouse_consignment', _('Consignment')).id
                consignment_route = self.env['stock.location.route'].browse(consignment_route_id)
            except UserError:
                pass
            if consignment_route and consignment_route in product_routes:
                is_available = True

        return is_available
