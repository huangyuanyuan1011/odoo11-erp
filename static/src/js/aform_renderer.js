odoo.define('flow.FormRenderer', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

var flowFormRenderer = FormRenderer.include({
    _render: function () {
        var self = this;
        var result = this._super.apply(this, arguments);
        $(".o_btn_flow").remove();
        if(typeof(this.state.res_id)==='number'){
            this._rpc({
                model: this.state.model,
                method: 'get_flow_btn',
                args: [[this.state.res_id]],
                context: {}
            }).then(function(result){
                if(result){
                    self.$flow_buttons = $(QWeb.render("flow.buttons", {'widget': result}));
                    $(".o_cp_buttons").first().append(self.$flow_buttons);
                    $('.o_btn_flow_submit').on('click', function () {
                        self.trigger_up('flow_action', {id:self.state.res_id, model:self.state.model, action: 'submit'});
                    });
                    $('.o_btn_flow_approve').on('click', function () {
                        self.trigger_up('flow_action', {id:self.state.res_id, model:self.state.model, action: 'approve'});
                    });
                    $('.o_btn_flow_refuse').on('click', function () {
                        self.trigger_up('flow_action', {id:self.state.res_id, model:self.state.model, action: 'refuse'});
                    });
                    $('.o_btn_flow_have_read').on('click', function () {
                        self.trigger_up('flow_action', {id:self.state.res_id, model:self.state.model, action: 'have_read'});
                    });
                    $('.o_btn_flow_chart').on('click', function (action) {
                        self.trigger_up('flow_chart_action', {id: parseInt(action.target.value)});
                    });
                }
            });
        }
        return result;
    },
});

return flowFormRenderer;

});
