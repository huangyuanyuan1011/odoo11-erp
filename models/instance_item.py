# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval, test_python_expr
from . import Push


class InstanceItem(models.Model):  # 实例条款
    _name = 'flow.instance_item'

    instance_id = fields.Many2one('flow.instance', related='activity_id.instance_id', string='实例')
    activity_id = fields.Many2one('flow.instance_activity', ondelete='cascade', string='活动')

    item_executor_ids = fields.One2many('flow.instance_item_executor', 'instance_item_id', string='项目执行人')
    is_pass = fields.Boolean(default=False, string='是否通过')
    parent_id = fields.Many2one('flow.instance_item', string='父级')
    children_id = fields.One2many('flow.instance_item', 'parent_id', string='子级')
    all_exec = fields.Boolean(default=False, string='是否全部执行')

    def __safe_eval_code(self, record, code):
        if code:
            eval_context = {
                'uid': self._uid,
                'user': self.env.user,
                # orm
                'self': record,
                # Deprecated use env or model instead
                'pool': self.pool,
                'cr': self._cr,
                'context': self._context,
            }
            safe_eval(code.strip(), locals_dict=eval_context,
                      mode="exec", nocopy=True)

    @api.one
    def submit(self, record, new_message):
        if not self.sudo().item_executor_ids.filtered(lambda r: r.res_users_id.id == self._uid):
            raise UserError(u'操作已过期')
        for out_id in self.activity_id.out_ids:
            if not out_id.act_to_id.executor_ids and not out_id.act_to_id.flow_stop:
                raise UserError('No executor')
            elif record.search([['id', '=', record.id]] + safe_eval(out_id.domain if out_id.domain else '[]')) \
                    and self.env['hr.employee'].search([['user_id', '=', self._uid]] + safe_eval(out_id.hr_domain if out_id.hr_domain else '[]')):
                self.sudo().item_executor_ids.filtered(lambda r: r.res_users_id.id == self._uid).is_pass = True
                #all_exec
                if self.all_exec:
                    if not self.sudo().item_executor_ids.filtered(lambda r: not r.is_pass):
                        self.sudo().is_pass = True
                    else:
                        return 'need all_exec'
                else:
                    self.sudo().is_pass = True
                    if self.sudo().item_executor_ids.__len__() > 1:
                        for item_executor_id in self.sudo().item_executor_ids:
                            if not item_executor_id.is_pass:
                                item_executor_id.unlink()
                if out_id.act_to_id.flow_stop:
                    self.__safe_eval_code(record, out_id.act_to_id.code)
                    return 'flow stopped'
                vals = {}
                vals['instance_id'] = self.instance_id.id
                vals['activity_id'] = out_id.act_to_id.id
                vals['parent_id'] = self.id
                vals['all_exec'] = out_id.act_to_id.all_exec
                item_id = self.sudo().create(vals)
                for executor_id in item_id.activity_id.executor_ids:
                    if executor_id.type == 'manager':
                        if not self.env.user.employee_ids[0].parent_id:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        exec_vals['res_users_id'] = self.env.user.employee_ids[0].parent_id.user_id.id
                        self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                    elif executor_id.type == 'creator':
                        if not record.create_uid:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        exec_vals['res_users_id'] = record.create_uid.id
                        self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                    elif executor_id.type == 'model_users':
                        if not record[executor_id.field_id.name]:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        for i in record[executor_id.field_id.name]:
                            exec_vals['res_users_id'] = i.id
                            self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                    else:
                        if not executor_id.sudo(self._uid).tag_id.employee_ids:
                            raise UserError('No executor')
                        for employee_id in executor_id.sudo(self._uid).tag_id.employee_ids:
                            if not employee_id.user_id:
                                raise UserError('No executor')
                            exec_vals = {}
                            exec_vals['instance_item_id'] = item_id.id
                            exec_vals['res_users_id'] = employee_id.user_id.id
                            self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                self.__safe_eval_code(record, out_id.act_to_id.code)
                return 'all_exec done'
            elif record.search([['id', '=', record.id]] + safe_eval(out_id.domain if out_id.domain else '[]')):
                self.sudo().item_executor_ids.filtered(lambda r: r.res_users_id.id == self._uid).is_pass = True
                #all_exec
                if self.all_exec:
                    if not self.sudo().item_executor_ids.filtered(lambda r: not r.is_pass):
                        self.sudo().is_pass = True
                    else:
                        return 'need all_exec'
                else:
                    self.sudo().is_pass = True
                    if self.sudo().item_executor_ids.__len__() > 1:
                        for item_executor_id in self.sudo().item_executor_ids:
                            if not item_executor_id.is_pass:
                                item_executor_id.unlink()
                if out_id.act_to_id.flow_stop:
                    self.__safe_eval_code(record, out_id.act_to_id.code)
                    return 'flow stopped'
                vals = {}
                vals['instance_id'] = self.instance_id.id
                vals['activity_id'] = out_id.act_to_id.id
                vals['parent_id'] = self.id
                vals['all_exec'] = out_id.act_to_id.all_exec
                item_id = self.sudo().create(vals)
                for executor_id in item_id.activity_id.executor_ids:
                    if executor_id.type == 'creator':
                        if not record.create_uid:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        exec_vals['res_users_id'] = record.create_uid.id
                        self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                    elif executor_id.type == 'model_users':
                        if not record[executor_id.field_id.name]:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        exec_vals['res_users_id'] = record[executor_id.field_id.name].id
                        self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                    else:
                        if not executor_id.sudo(self._uid).tag_id.employee_ids:
                            raise UserError('No executor')
                        for employee_id in executor_id.sudo(self._uid).tag_id.employee_ids:
                            if not employee_id.user_id:
                                raise UserError('No executor')
                            exec_vals = {}
                            exec_vals['instance_item_id'] = item_id.id
                            exec_vals['res_users_id'] = employee_id.user_id.id
                            self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(exec_vals)
                self.__safe_eval_code(record, out_id.act_to_id.code)
                return 'all_exec done'
        raise UserError('domain:%s,hr_domain:%s' % (out_id.domain, out_id.hr_domain))

    @api.one
    def approve(self, record, new_message):
        return self.submit(record, new_message)

    @api.one
    def refuse(self, record, new_message):
        if not self.sudo().item_executor_ids.filtered(lambda r: r.res_users_id.id == self._uid):
            raise UserError(u'操作已过期')
        self.sudo().parent_id.is_pass = False
        self.sudo().parent_id.item_executor_ids.unlink()
        item_id = self.sudo().parent_id
        if item_id.activity_id.flow_start:
            exec_vals = {}
            exec_vals['instance_item_id'] = item_id.id
            exec_vals['res_users_id'] = record.create_uid.id
            self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(
                exec_vals)
        else:
            for executor_id in item_id.activity_id.executor_ids:
                if executor_id.type == 'manager':
                    if not self.env.user.employee_ids[0].parent_id:
                        raise UserError('No executor')
                    exec_vals = {}
                    exec_vals['instance_item_id'] = item_id.id
                    exec_vals['res_users_id'] = self.env.user.employee_ids[0].parent_id.user_id.id
                    self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(
                        exec_vals)
                elif executor_id.type == 'creator':
                    if not record.create_uid:
                        raise UserError('No executor')
                    exec_vals = {}
                    exec_vals['instance_item_id'] = item_id.id
                    exec_vals['res_users_id'] = record.create_uid.id
                    self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(
                        exec_vals)
                elif executor_id.type == 'model_users':
                    if not record[executor_id.field_id.name]:
                        raise UserError('No executor')
                    exec_vals = {}
                    exec_vals['instance_item_id'] = item_id.id
                    exec_vals['res_users_id'] = record[executor_id.field_id.name].id
                    self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(
                        exec_vals)
                else:
                    if not executor_id.sudo(self._uid).tag_id.employee_ids:
                        raise UserError('No executor')
                    for employee_id in executor_id.sudo(self._uid).tag_id.employee_ids:
                        if not employee_id.user_id:
                            raise UserError('No executor')
                        exec_vals = {}
                        exec_vals['instance_item_id'] = item_id.id
                        exec_vals['res_users_id'] = employee_id.user_id.id
                        self.sudo().env['flow.instance_item_executor'].with_context(new_message=new_message).create(
                            exec_vals)
        self.__safe_eval_code(record, self.parent_id.activity_id.code)
        self.sudo().unlink()
        return 'ok'

    @api.one
    def have_read(self, record, new_message):
        return self.submit(record, new_message)


class InstanceItemExecutor(models.Model):
    _name = 'flow.instance_item_executor'  # 实例条款人

    instance_id = fields.Many2one('flow.instance', related='instance_item_id.instance_id', string='实例')
    instance_item_id = fields.Many2one('flow.instance_item', ondelete='cascade', string='实例项目')

    res_users_id = fields.Many2one('res.users', string='用户')
    is_pass = fields.Boolean(default=False, string='是否通过')

    @api.one
    def _get_record_data(self):
        record_id = self.env[self.instance_id.model_id.model].browse(self.instance_id.res_id)
        self.record_name = record_id.sudo().name
        self.record_create_date = record_id.sudo().create_date
        self.record_company_name = record_id.sudo().company_id.name if getattr(record_id.sudo(), 'company_id', False) else ''
        if 'state' in record_id.sudo()._fields:
            try:
                self.record_state = [i for i in record_id.sudo()._fields['state'].selection if i[0] == record_id.sudo().state][0][1]
            except:
                pass

    record_name = fields.Char(compute='_get_record_data', string='名称')
    record_model_name = fields.Char(related='instance_id.model_id.name', string='模型说明')
    record_create_date = fields.Datetime(compute='_get_record_data', string='创建时间')
    record_company_name = fields.Char(compute='_get_record_data', string='公司名称')
    record_state = fields.Char(compute='_get_record_data', string='状态')

    @api.multi
    def goto(self):
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.instance_id.model_id.model,
            'view_id': False,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'res_id': self.instance_id.res_id,
        }

    @api.model
    def create(self, vals):
        new_executor = super(InstanceItemExecutor, self).create(vals)
        new_message = self._context.get('new_message')
        if new_message:
            new_executor.res_users_id.partner_id._notify(new_message, force_send=True)
            new_message.needaction_partner_ids = [(6, 0, new_executor.res_users_id.partner_id.ids)]
        account_ids = [new_executor.res_users_id.id]
        body = new_executor.record_model_name
        iOSExtParameters = {'extParameters': {
            'method': 'goto',
            'res_model': new_executor._name,
            'res_id': new_executor.id,
        }}
        Push.create_request(account_ids, body, iOSExtParameters)
        return new_executor

