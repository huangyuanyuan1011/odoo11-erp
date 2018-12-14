odoo.define('flow.InsDiagramModel', function (require) {
"use strict";

var BasicModel = require('web.BasicModel');

/**
 * DiagramModel
 */
var InsDiagramModel = BasicModel.extend({
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @returns {Object}
     */
    get: function (id, options) {
        return $.extend(true, this._super.apply(this, arguments), {
            nodes: this.datanodes,
            edges: this.edges,
            res_id: this.res_id,
            id: id,
            model_id: this.model_id,
            node_model: this.node_model,
            connector_model: this.connector_model,
        });
    },
    /**
     * @override
     * @param {Object} params
     * @returns {Deferred}
     */
    load: function (params) {
        this.modelName = params.modelName;
        this.res_id = params.res_id;
        var d2 = this._fetchDiagramInfo(params.modelName, params.res_id);
        return $.when(this._super.apply(this, arguments), d2);
    },
    reload: function (id, options) {
        options = options || {};
        var element = this.localData[id];
        if (options.offset !== undefined) {
            this._setOffset(element.id, options.offset);
        }
        if (options.currentId !== undefined) {
            element.res_id = options.currentId;
        }
        this.modelName = element.model;
        this.res_id = element.res_id;
        var d2 = this._fetchDiagramInfo(element.model, element.res_id);
        return $.when(this._super.apply(this, arguments), d2);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {any} record
     * @returns {Deferred}
     */
    _fetchDiagramInfo: function (model, res_id) {
        var self = this;
        var route = '/flow/get_diagram_instance';
        return this._rpc({
            route: route,
            params: {
                id: res_id,
                modelName: model,
            },
        }/*,{async: false}*/).then(function (data) {
            self.datanodes = data.nodes;
            self.edges = data.conn;
            self.model_id = data.model_id;
            self.node_model = data.node_model;
            self.connector_model = data.connector_model;
        });
    },
});

return InsDiagramModel;
});
