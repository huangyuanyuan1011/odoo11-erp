# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID, tools
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import config, graph, ConstantMapping, SKIPPED_ELEMENT_TYPES


class Instance(models.Model):  # 实例
    _name = 'flow.instance'

    @api.one
    def name_get(self):
        return self.id, 'Chart'
    # name = fields.Char()
    model_id = fields.Many2one('ir.model', string='模型')  # 多个实例对应一个模块
    flow_id = fields.Many2one('flow.flow', string='流程')  # 多个实例对应一个流程
    activity_ids = fields.One2many('flow.instance_activity', 'instance_id', string='活动')  # 一个实例对应多个实例活动
    res_id = fields.Integer(string='资源')
    instance_item_ids = fields.One2many('flow.instance_item', 'instance_id', string='实例项目')  # 一个实例对应多个实例项目

    @api.model
    def create(self, vals):     #创建时复制一份信息
        result = super(Instance, self).create(vals)         #在super机制里可以保证公共父类仅被执行一次，调用父类的方法。
        for act_id in result.flow_id.activity_ids:
            act_vals = {}
            act_vals['name'] = act_id.name
            act_vals['instance_id'] = result.id
            act_vals['flow_start'] = act_id.flow_start
            act_vals['flow_stop'] = act_id.flow_stop
            act_vals['all_exec'] = act_id.all_exec
            act_vals['type'] = act_id.type
            act_vals['code'] = act_id.code
            instance_activity_id = self.env['flow.instance_activity'].create(act_vals)
            for executor_id in act_id.executor_ids:
                exe_vals = {}
                exe_vals['activity_id'] = instance_activity_id.id
                exe_vals['type'] = executor_id.type
                exe_vals['tag_id'] = executor_id.tag_id.id
                exe_vals['field_id'] = executor_id.field_id.id
                self.env['flow.instance_executor'].create(exe_vals)
        for tra_id in result.flow_id.transition_ids:
            tra_vals = {}
            tra_vals['act_from_id'] = result.activity_ids.filtered(lambda r: r.name == tra_id.act_from_id.name).id
            tra_vals['act_to_id'] = result.activity_ids.filtered(lambda r: r.name == tra_id.act_to_id.name).id
            tra_vals['domain'] = tra_id.domain
            tra_vals['model_id'] = tra_id.model_id.id
            tra_vals['model'] = tra_id.model
            tra_vals['hr_domain'] = tra_id.hr_domain
            self.env['flow.instance_transition'].create(tra_vals)
        ins_item_vals = {}
        ins_item_vals['activity_id'] = result.activity_ids.filtered(lambda r: r.flow_start).id
        instance_item_id = self.env['flow.instance_item'].create(ins_item_vals)
        instance_item_executor_vals = {}
        instance_item_executor_vals['instance_item_id'] = instance_item_id.id
        instance_item_executor_vals['res_users_id'] = self._context.get('create_user_id') or self._uid
        self.env['flow.instance_item_executor'].create(instance_item_executor_vals)
        return result

    @api.one
    def _flow_action(self, action, record):
        action_f = getattr(self.instance_item_ids.filtered(lambda r: not r.is_pass), action)
        action_str = ''
        if action == 'submit':
            action_str = _('提交')
        elif action == 'approve':
            action_str = _('批准')
        elif action == 'refuse':
            action_str = _('拒绝')
        else:
            action_str = _('已读')
        new_message = record.sudo().message_post(body=self.env.user.name + ',' + action_str,
                                                 subtype=u'mail.mt_comment')
        return action_f(record, new_message)

    def _get_flow_btn(self):
        result = {'submit': False, 'approval': False, 'have_read': False, 'instance_id': self.id}
        instance_item_executor_id = self.env['flow.instance_item_executor'] \
            .search([['is_pass', '=', False],
                     ['instance_id', '=', self.id],
                     ['res_users_id', '=', self._uid]])
        if instance_item_executor_id:
            activity_id = instance_item_executor_id.instance_item_id.activity_id
            if activity_id.flow_start:
                type = 'submit'
            else:
                type = activity_id.type
            result[type] = True
        return result

    def graph_get(self, scale):
        def compute_node(act):
            if act.flow_stop:
                return
            else:
                for out_id in act.out_ids:
                    transitions.append(('act_' + str(act.id), 'act_' + str(out_id.act_to_id.id)))
                    tres['tra_' + str(out_id.id)] = ('act_' + str(act.id), 'act_' + str(out_id.act_to_id.id))
                    if 'act_' + str(out_id.act_to_id.id) not in nodes:
                        nodes.append('act_' + str(out_id.act_to_id.id))
                        compute_node(out_id.act_to_id)

        nodes = []
        transitions = []
        start = []
        tres = {}

        for item in self.instance_item_ids:
            nodes.append('item_' + str(item.id))
            if not item.parent_id:
                start.append('item_' + str(item.id))
            if item.children_id:
                transitions.append(('item_' + str(item.id), 'item_' + str(item.children_id.id)))
                tres['item_' + str(item.children_id.id)] = ('item_' + str(item.id), 'item_' + str(item.children_id.id))
            elif not item.is_pass:
                not_is_pass = ('item_' + str(item.id), 'act_' + str(item.activity_id.id))
                for out_id in item.activity_id.out_ids:
                    transitions.append(('item_' + str(item.id), 'act_' + str(out_id.act_to_id.id)))
                    tres['itemtra_' + str(out_id.id)] = ('item_' + str(item.id), 'act_' + str(out_id.act_to_id.id))

                    nodes.append('act_' + str(out_id.act_to_id.id))
                    compute_node(out_id.act_to_id)

        nodes = list(set(nodes))

        g = graph(nodes, transitions, [])
        g.process(start)
        g.scale(*scale)
        result = g.result_get()
        results = {}
        for k, v in result.items():
            if isinstance(k, str):
                results[k] = v

        blank_nodes = []
        for act in self.activity_ids:
            if not act.out_ids and not act.in_ids:
                blank_nodes.append({'id': 'act_' + str(act.id), 'name': act.name})

        y = map(lambda t: t['y'], filter(lambda x: x['y'] if x['x'] == 20 else None, results.values()))
        y_max = (y and max(y)) or 120

        for blnk_node in blank_nodes:
            y_max += 140
            blnk_node.update(x=20, y=y_max)
            results[blnk_node['id']] = blnk_node
        try:
            result[not_is_pass[0]].update(act_id=not_is_pass[1])
        except:
            pass

        return {'nodes': results,
                'transitions': tres}

    def get_diagram_instance(self, scale):
        graphs = self.graph_get(scale)

        nodes = graphs['nodes']
        transitions = graphs['transitions']
        connectors = {}

        def _get_tra_label(tra):
            tra = tra.split('_')
            if tra[0] == 'tra':
                tra_id = self.env['flow.instance_transition'].browse([int(tra[1])])
                return (tra_id.domain or '') + (tra_id.hr_domain or '')
            else:
                return ''

        for tr in transitions:
            connectors.setdefault(tr, {
                'id': tr,
                's_id': transitions[tr][0],
                'd_id': transitions[tr][1],
                'label': _get_tra_label(tr)
            })

        def _get_act_label(act):
            act = act.split('_')
            if act[0] == 'act':
                instance_activity = self.env['flow.instance_activity'].browse([int(act[1])])
                color = 'gray' if instance_activity.flow_start or instance_activity.flow_stop else 'white'
                return instance_activity.name, color
            else:
                label = ''
                instance_item = self.env['flow.instance_item'].browse([int(act[1])])
                color = 'gray' if instance_item.activity_id.flow_start or instance_item.activity_id.flow_stop else 'white'
                for item_executor_id in instance_item.item_executor_ids:
                    label += item_executor_id.sudo().res_users_id.name + ','
                return label, color

        for act in nodes:
            nodes[act]['id'] = act
            nodes[act]['name'], nodes[act]['color'] = _get_act_label(act)

            if 'act_id' in nodes[act]:
                nodes[act]['color'] = 'red'

        return dict(nodes=nodes, conn=connectors, model_id=self.model_id.id,
                    node_model='flow.instance_activity',
                    connector_model='flow.instance_transition')


class InstanceActivity(models.Model):  # 实例活动
    _name = 'flow.instance_activity'

    name = fields.Char(string='名称')
    instance_id = fields.Many2one('flow.instance', ondelete='cascade', string='实例')  # 多个实例活动 对应 一个 实例
    model_id = fields.Many2one('ir.model', related='instance_id.model_id', string='模型')  # 多个实例对应一个模块
    out_ids = fields.One2many('flow.instance_transition', 'act_from_id', string='出项')
    in_ids = fields.One2many('flow.instance_transition', 'act_to_id', string='入项')
    flow_start = fields.Boolean(string='流程开始')
    flow_stop = fields.Boolean(string='流程结束')
    all_exec = fields.Boolean(default=False, string='是否全部执行')
    type = fields.Selection([('submit', '提交'),
                             ('approval', '审核'),
                             ('have_read', '知会')], required=True, default='approval', string='类型')

    executor_ids = fields.One2many('flow.instance_executor', 'activity_id', string='执行人')
    instance_item_ids = fields.One2many('flow.instance_item', 'activity_id', string='实例项目')

    code = fields.Text(string='编码')


class InstanceExecutor(models.Model):
    _name = 'flow.instance_executor'

    activity_id = fields.Many2one('flow.instance_activity', ondelete='cascade', string='活动')
    model_id = fields.Many2one('ir.model', related='activity_id.model_id', string='模型')  # 多个实例对应一个模块

    type = fields.Selection([('tag', '标签'),
                             ('manager', '管理者'),
                             ('creator', '创建人'),
                             ('model_users', '模型用户字段')], string='类型')
    field_id = fields.Many2one('ir.model.fields', string='字段')
    tag_id = fields.Many2one('hr.employee.category', string='标签')


class InstanceTransition(models.Model):
    _name = 'flow.instance_transition'

    # name = fields.Char()
    act_from_id = fields.Many2one('flow.instance_activity', ondelete='cascade', string='活动来源')
    act_to_id = fields.Many2one('flow.instance_activity', ondelete='cascade', string='活动去向')

    domain = fields.Char(string='条件')
    model_id = fields.Many2one('ir.model', required=True, domain=[('transient', '=', False)], readonly=True, string='模型')
    model = fields.Char(related='model_id.model', readonly=True, string='模型名称')

    hr_domain = fields.Char(string='员工条件')

