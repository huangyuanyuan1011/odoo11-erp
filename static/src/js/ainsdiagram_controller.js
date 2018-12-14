odoo.define('flow.InsDiagramController', function (require) {
"use strict";

var BasicController = require('web.BasicController');
var core = require('web.core');
var Dialog = require('web.Dialog');
var view_dialogs = require('web.view_dialogs');

var _t = core._t;
var QWeb = core.qweb;
var FormViewDialog = view_dialogs.FormViewDialog;

/**
 * Diagram Controller
 */
var InsDiagramController = BasicController.extend({
    className: 'o_diagram_view',
    custom_events: {
        add_edge: '_onAddEdge',
        edit_edge: '_onEditEdge',
        edit_node: '_onEditNode',
        remove_edge: '_onRemoveEdge',
        remove_node: '_onRemoveNode',
    },

    _pushState: function (state) {
        state = state || {};
        var env = this.model.get(this.handle, {env: true});
        state.id = env.currentId;
        this._super(state);
    },
    /**
     * @override
     * @param {Widget} parent
     * @param {DiagramModel} model
     * @param {DiagramRenderer} renderer
     * @param {Object} params
     */
//    init: function (parent, model, renderer, params) {
//        this._super.apply(this, arguments);
//        this.domain = params.domain || [];
//        this.context = params.context;
//        this.ids = params.ids;
//        this.currentId = params.currentId;
//    },
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Render the buttons according to the DiagramView.buttons template and add
     * listeners on it. Set this.$buttons with the produced jQuery element
     *
     * @param {jQuery} [$node] a jQuery node where the rendered buttons should
     *   be inserted $node may be undefined, in which case they are inserted
     *   into this.options.$buttons
     */
    renderButtons: function ($node) {
        this.$buttons = $(QWeb.render("DiagramView.buttons", {widget: this}));
        this.$buttons.on('click', '.o_diagram_new_button', this._addNode.bind(this));
        this.$buttons.appendTo($node);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Creates a popup to add a node to the diagram
     *
     * @private
     */
    _addNode: function () {
        var self = this;
        var state = this.model.get();
        var pop = new FormViewDialog(this, {
            res_model: state.node_model,
            domain: this.domain,
            context: {'default_flow_id':state.res_id, 'default_instance_id':state.res_id},
            title: _.str.sprintf("%s %s", _t("Create:"), _t('Activity')),
            disable_multiple_selection: true,
        }).open();
        pop.on('closed', this, this.reload.bind(this));
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Custom event handler that opens a popup to add an edge from given source
     * and dest nodes.
     *
     * @private
     * @param {OdooEvent} event
     */
    _onAddEdge: function (event) {
        var self = this;
        var state = this.model.get();
        var pop = new FormViewDialog(self, {
            res_model: state.connector_model,
            domain: this.domain,
            context: {
                'default_flow_id':state.res_id,
                'default_instance_id':state.res_id,
                'default_model_id':state.model_id,
                'default_act_from_id':event.data.source_id,
                'default_act_to_id':event.data.dest_id,
            },
            title: _.str.sprintf("%s %s", _t("Create:"), _t('Transition')),
            disable_multiple_selection: true,
        }).open();
        pop.on('closed', this, this.reload.bind(this));
    },
    /**
     * Custom event handler that opens a popup to edit an edge given its id
     *
     * @private
     * @param {OdooEvent} event
     */
    _onEditEdge: function (event) {
        var state = this.model.get();
        new FormViewDialog(this, {
            res_model: state.connector_model,
            res_id: parseInt(event.data.id, 10),
            context: this.context,
            title: _.str.sprintf("%s %s", _t("Open:"), _t('Transition')),
            on_saved: this.reload.bind(this),
        }).open();
    },
    /**
     * Custom event handler that opens a popup to edit the content of a node
     * given its id
     *
     * @private
     * @param {OdooEvent} event
     */
    _onEditNode: function (event) {
        var state = this.model.get();
        new FormViewDialog(this, {
            res_model: state.node_model,
            res_id: event.data.id,
            context: this.context,
            title: _.str.sprintf("%s %s", _t("Open:"), _t('Activity')),
            on_saved: this.reload.bind(this),
        }).open();
    },
    /**
     * Custom event handler that removes an edge given its id
     *
     * @private
     * @param {OdooEvent} event
     */
    _onRemoveEdge: function (event) {
        var self = this;
        var state = self.model.get();
        self._rpc({
            model: state.connector_model,
            method: 'unlink',
            args: [event.data.id],
        });
    },
    /**
     * Custom event handler that removes a node given its id
     *
     * @private
     * @param {OdooEvent} event
     */
    _onRemoveNode: function (event) {
        var self = this;
        var state = self.model.get();
        self._rpc({
            model: state.node_model,
            method: 'unlink',
            args: [event.data.id],
        });
    },
});

return InsDiagramController;

});
