odoo.define('flow.view_registry', function (require) {
"use strict";

var field_utils = require('web.field_utils');
var core = require('web.core');
var _lt = core._lt;
core.search_filters_registry.map.datetime.include({
    get_tz_value: function(type, value){
        if(type=='date'){
            return value
        }else{
            return value && value.add(-this.getSession().getTZOffset(value), 'minutes');
        }
    },
    get_domain: function (field, operator) {
        switch (operator.value) {
        case '∃':
            return [[field.name, '!=', false]];
        case '∄':
            return [[field.name, '=', false]];
        case 'between':
            return [[field.name, '>=', this.get_tz_value(field.type, this.get_value())], [field.name, '<=', this.get_tz_value(field.type, this.get_value(1))]];
        default:
            return [[field.name, operator.value, this.get_tz_value(field.type, this.get_value())]];
        }
    },
    toString: function () {
        var str = field_utils.format[this.attributes.type](this.get_value(), {type: this.attributes.type}, {timezone: false});
        var date_1_value = this.datewidget_1 && this.get_value(1);
        if (date_1_value) {
            str += _lt(" and ") + field_utils.format[this.attributes.type](date_1_value, {type: this.attributes.type}, {timezone: false});
        }
        return str;
    },
});

var view_registry = require('web.view_registry');

var InsDiagramView = require('flow.InsDiagramView');

view_registry.add('aInsDiagram', InsDiagramView);

});
