define([
        'jquery',
        'backbone'
    ],
    function ($, Backbone) {
        'use strict';

        return Backbone.View.extend({
            className: 'alert',

            initialize: function (options) {
                this.level = options.level || 'info';
                this.title = options.title || '';
                this.message = options.message || '';
            },

            render: function () {
                var body = '';
                if (this.title) {
                    body += '<strong>' + this.title + '</strong> ';
                }
                body += this.message;
                this.$el.addClass('alert-' + this.level).attr('role', 'alert').html(body);
                return this;
            }
        });
    }
);
