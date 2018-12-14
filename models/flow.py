# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.tools import config, graph, ConstantMapping, SKIPPED_ELEMENT_TYPES


class Flow(models.Model):
    _name = 'flow.flow'

    name = fields.Char()
    model_id = fields.Many2one('ir.model', string='模型')      # 这个审批流对应的模块
    activity_ids = fields.One2many('flow.activity', 'flow_id', string='活动')  # 1 对 多 个 活动
    transition_ids = fields.One2many('flow.transition', 'flow_id', string='转换')  # 1个审批对多个节点
    is_valid = fields.Boolean(string='有效')

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
        if not self.activity_ids:
            return {'nodes': {}, 'transitions': tres}
        start_act_id = list(filter(lambda r: r.flow_start, self.activity_ids))[0]
        start.append('act_' + str(start_act_id.id))
        nodes.append('act_' + str(start_act_id.id))
        compute_node(start_act_id)

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

        return {'nodes': results, 'transitions': tres}

    def get_diagram_instance(self, scale):
        graphs = self.graph_get(scale)

        nodes = graphs['nodes']
        transitions = graphs['transitions']
        connectors = {}

        def _get_tra_label(tra):
            tra = tra.split('_')
            if tra[0] == 'tra':
                tra_id = self.env['flow.transition'].browse([int(tra[1])])
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
                instance_activity = self.env['flow.activity'].browse([int(act[1])])
                color = 'gray' if instance_activity.flow_start or instance_activity.flow_stop else 'white'
                return instance_activity.name, color

        for act in nodes:
            nodes[act]['id'] = act
            nodes[act]['name'], nodes[act]['color'] = _get_act_label(act)

            if 'act_id' in nodes[act]:
                nodes[act]['color'] = 'red'

        return dict(nodes=nodes, conn=connectors, model_id=self.model_id.id,
                    node_model = 'flow.activity',
                    connector_model = 'flow.transition')


class Executor(models.Model):  # 执行人
    _name = 'flow.executor'

    activity_id = fields.Many2one('flow.activity', ondelete='cascade', string='活动')  # 多个执行人对应一个活动

    type = fields.Selection([('tag', '职位(标签)'),        # 标签，名称
                             ('manager', '管理者'),  # 经理
                             ('creator', '创建人'),  # 创建者
                             ('model_users', '模型用户字段')], string='类型')  # 模型上的user_id字段
    model_id = fields.Many2one('ir.model', related='activity_id.flow_id.model_id', readonly=True, string='模型')
    field_id = fields.Many2one('ir.model.fields', string='字段')
    tag_id = fields.Many2one('hr.employee.category', ondelete='restrict', string='标签')  # hr 员工种类


class Activity(models.Model):  # 活动
    _name = 'flow.activity'

    name = fields.Char(string='名字')
    flow_id = fields.Many2one('flow.flow', ondelete='cascade', string='流程')  # 多个活动对1个流程
    out_ids = fields.One2many('flow.transition', 'act_from_id', string='出项')  # 一个活动对多个节点（出）
    in_ids = fields.One2many('flow.transition', 'act_to_id', string='入项')  # 一个活动对多个节点（进）

    flow_start = fields.Boolean(string='流程开始')  # 流程 开始
    flow_stop = fields.Boolean(string='流程结束')  # 流程 结束
    all_exec = fields.Boolean(default=False, string='是否全部执行')  # 是否执行 会签
    type = fields.Selection([('submit', '提交'),
                             ('approval', '批准'),
                             ('have_read', '已读')], required=True, default='approval', string='类型')  # 申请、审批、知会

    executor_ids = fields.One2many('flow.executor', 'activity_id', string='执行人')  # 1 对 多 执行人

    code = fields.Text(string='编码')

    model_id = fields.Many2one('ir.model', related='flow_id.model_id', readonly=True, string='模型')

    @api.constrains('code')
    def _check_python_code(self):
        for action in self.filtered('code'):
            msg = test_python_expr(expr=action.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)


# 转换
class Transition(models.Model):
    _name = 'flow.transition'

    # name = fields.Char()
    flow_id = fields.Many2one('flow.flow', related='act_from_id.flow_id', readonly=True, string='流程')  # 多个节点对应一个流程
    act_from_id = fields.Many2one('flow.activity', ondelete='cascade', string='活动来源')  # 多个节点对应一个活动（进）
    act_to_id = fields.Many2one('flow.activity', ondelete='cascade', string='活动去向')  # 多个节点对应一个活动（出）

    domain = fields.Char(string='条件')
    model_id = fields.Many2one('ir.model', required=True, related='flow_id.model_id', string='模型')
    model = fields.Char(related='model_id.model', readonly=True, string='模型名称')

    hr_domain = fields.Char(string='员工条件')

    @api.one
    @api.constrains('act_from_id', 'act_to_id')
    def _check_constrains(self):
        if self.act_from_id and self.act_to_id:
            pass
        else:
            raise ValidationError("Fields act_from_id and act_to_id must not be False")