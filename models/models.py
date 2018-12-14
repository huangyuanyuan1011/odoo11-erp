

# -*- coding: utf-8 -*-
from odoo import models, api

@api.multi
def get_flow_btn(self):
    model_id = self.env['ir.model'].search([['model', '=', self._name]])
    instance_id = self.env['flow.instance'].search([['res_id', '=', self.id], ['model_id', '=', model_id.id]])
    if instance_id:
        return instance_id._get_flow_btn()
models.Model.get_flow_btn = get_flow_btn

