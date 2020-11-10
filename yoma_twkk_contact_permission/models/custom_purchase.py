from lxml import etree
from odoo import fields,api,tools,models

class custom_po(models.Model):
    _inherit = "res.partner"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(custom_po, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
        group_id = self.env.user.has_group('yoma_twkk_contact_permission.group_hide_create_button_PO')
        doc = etree.XML(res['arch'])
        if group_id:
            if view_type == 'tree':
                nodes = doc.xpath("//tree[@string='Contacts']")
                for node in nodes:
                    node.set('create', '0')
                res['arch'] = etree.tostring(doc)
            if view_type == 'form':
                nodes = doc.xpath("//form[@string='Partners']")
                for node in nodes:
                    node.set('create', '0')
                res['arch'] = etree.tostring(doc)
            if view_type == 'kanban':
                nodes = doc.xpath("//kanban[@class='o_res_partner_kanban']")
                for node in nodes:
                    node.set('create', '0')
                res['arch'] = etree.tostring(doc)


        return res