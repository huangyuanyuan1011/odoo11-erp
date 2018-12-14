# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
from lxml import etree


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('aInsDiagram', 'aInsDiagram')], string='类型')
