# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.http as http

from odoo.tools.safe_eval import safe_eval


class DiagramView(http.Controller):
    @http.route('/flow/get_diagram_instance', type='json', auth='user')
    def get_diagram_instance(self, req, id, modelName, **kw):
        instance = req.env[modelName]
        return instance.browse([id]).get_diagram_instance((140, 180))
