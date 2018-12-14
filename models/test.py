# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError


class Test(models.Model):
    _name = 'flow.test'
    _description = '流程测试'
    _inherit = 'mail.thread'

    name = fields.Char(string='名称')
    user_id = fields.Many2one('res.users', default=lambda r: r._uid, string='用户ID')
    string = fields.Char(compute='_get_string', store=True, string='用户名称')

    @api.one
    def confirm(self):
        self.name = 'confirm'

    @api.one
    @api.depends('user_id', 'user_id.name')
    def _get_string(self):
        self.string = self.user_id.name