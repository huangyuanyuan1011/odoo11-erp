# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def create(self, values):
        result = super(MailThread, self).create(values)
        if 'flow.flow' in self.env:
            model_id = self.env['ir.model'].search([['model', '=', result._name]])
            flow_id = self.env['flow.flow'].search([['model_id', '=', model_id.id]])
            if flow_id and flow_id.is_valid:
                self.sudo().env['flow.instance'].with_context(create_user_id=self._uid).create({'model_id': model_id.id, 'flow_id': flow_id.id, 'res_id': result.id})
        return result

    @api.one
    def reset_flow(self):
        if 'flow.flow' in self.env:
            model_id = self.env['ir.model'].search([['model', '=', self._name]])
            flow_id = self.env['flow.flow'].search([['model_id', '=', model_id.id]])
            if flow_id:
                instance_id = self.env['flow.instance'].search([['flow_id', '=', flow_id.id], ['res_id', '=', self.id]])
                instance_id.sudo().unlink()
                instance_id.sudo().with_context(create_user_id=self.create_uid.id).create({'model_id': model_id.id,
                                                                                           'flow_id': flow_id.id,
                                                                                           'res_id': self.id})

    @api.one
    def reset_flow_submit(self):
        if 'flow.flow' in self.env:
            model_id = self.env['ir.model'].search([['model', '=', self._name]])
            flow_id = self.env['flow.flow'].search([['model_id', '=', model_id.id]])
            if flow_id:
                instance_id = self.env['flow.instance'].search([['flow_id', '=', flow_id.id], ['res_id', '=', self.id]])
                instance_id.sudo().unlink()
                instance_id.sudo().with_context(create_user_id=self.create_uid.id).create({'model_id': model_id.id,
                                                                                           'flow_id': flow_id.id,
                                                                                           'res_id': self.id})
                return instance_id._flow_action('submit', self)


    @api.one
    def unlink(self):
        super(MailThread, self).unlink()
        if 'flow.flow' in self.env:
            model_id = self.env['ir.model'].search([['model', '=', self._name]])
            instance_id = self.env['flow.instance'].search([['model_id', '=', model_id.id], ['res_id', '=', self.id]])
            if instance_id:
                instance_id.sudo().unlink()

    @api.multi
    def flow_action(self, action):
        model_id = self.env['ir.model'].search([['model', '=', self._name]])
        return self.env['flow.instance'].search([['res_id', '=', self.id], ['model_id', '=', model_id.id]])._flow_action(action, self)

    @api.one
    def write(self, vals):
        for key, val in vals.items():
            readonly = self._fields[key].readonly
            if self._fields[key].states:
                if self.state in self._fields[key].states:
                    for k, v in self._fields[key].states[self.state]:
                        if k == 'readonly':
                            readonly = v
            if readonly and self._uid != SUPERUSER_ID:
                raise AccessError("不能修改只读的字段！")
        return super(MailThread, self).write(vals)
