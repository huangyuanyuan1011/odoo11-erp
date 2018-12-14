odoo.define('flow.FormController', function (require) {
"use strict";

var FormController = require('web.FormController');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

var flowFormController = FormController.include({
    custom_events: _.extend({}, FormController.prototype.custom_events, {
        flow_chart_action: '_flow_chart_action',
        flow_action: '_flow_action',
    }),
    _flow_chart_action: function(action) {
        var self = this;
        this.do_action({
            type:'ir.actions.act_window',
            res_model: 'flow.instance',
            views: [[false,'aInsDiagram']],
            target: 'current',
            res_id: action.data.id,
            context: {},
        }, {
            on_close: function () {
                return self.reload();
            },
        });
    },
    _flow_action: function(action) {
        var self = this;
        self._rpc({
            model: action.data.model,
            method: 'flow_action',
            args: [[action.data.id], action.data.action],
            context: {},
        }).then(function(result){
            console.log(result);
            self.reload();
        });
    },
    renderButtons: function ($node) {
        var self = this;
        this._super($node);
        if($node){
            $node.find('div').first().css({"float": "left"});
        }
    },
});

return flowFormController;

});
