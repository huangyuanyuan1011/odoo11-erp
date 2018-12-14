odoo.define('flow.InsDiagramView', function (require) {
"use strict";

var BasicView = require('web.BasicView');
var core = require('web.core');
var InsDiagramModel = require('flow.InsDiagramModel');
var InsDiagramRenderer = require('flow.InsDiagramRenderer');
var InsDiagramController = require('flow.InsDiagramController');

var _lt = core._lt;

/**
 * Diagram View
 */
var InsDiagramView = BasicView.extend({
    display_name: _lt('Diagram'),
    icon: 'fa-code-fork',
    multi_record: false,
    searchable: false,
    jsLibs: [[
        '/flow/static/lib/js/jquery.mousewheel.js',
        '/flow/static/lib/js/raphael.js',
    ]],
    config: {
        Model: InsDiagramModel,
        Renderer: InsDiagramRenderer,
        Controller: InsDiagramController,
    },
});

return InsDiagramView;

});
