define([
        'jquery',
        'backbone',
        'underscore',
        'underscore.string',
        'moment',
        'text!templates/coupon_list.html',
        'dataTablesBootstrap'
    ],
    function ($,
              Backbone,
              _,
              _s,
              moment,
              CouponListViewTemplate) {

        'use strict';

        return Backbone.View.extend({
            className: 'coupon-list-view',
            downloadTpl: _.template('<a href="" class="btn btn-secondary btn-small ' +
                'voucher-report-button" data-coupon-id="<%= id %>">' +
                '<%= gettext(\'Download Coupon Report\') %></a>'),

            events: {
                'click .voucher-report-button': 'downloadVoucherReport'
            },

            template: _.template(CouponListViewTemplate),

            initialize: function () {
                _.bindAll(this, 'downloadVoucherReport');
                this.listenTo(this.collection, 'update', this.refreshTableData);
            },

            getRowData: function (coupon) {
                return {
                    id: coupon.get('id'),
                    title: coupon.get('title')
                };
            },

            renderCouponTable: function () {
                var filterPlaceholder = gettext('Search...'),
                    $emptyLabel = '<label class="sr">' + filterPlaceholder + '</label>';

                if (!$.fn.dataTable.isDataTable('#couponTable')) {
                    this.$el.find('#couponTable').DataTable({
                        autoWidth: false,
                        info: true,
                        paging: true,
                        oLanguage: {
                            oPaginate: {
                                sNext: gettext('Next'),
                                sPrevious: gettext('Previous')
                            },

                            // Translators: _START_, _END_, and _TOTAL_ are placeholders. Do NOT translate them.
                            sInfo: gettext('Displaying _START_ to _END_ of _TOTAL_ coupons'),

                            // Translators: _MAX_ is a placeholder. Do NOT translate it.
                            sInfoFiltered: gettext('(filtered from _MAX_ total coupons)'),

                            // Translators: _MENU_ is a placeholder. Do NOT translate it.
                            sLengthMenu: gettext('Display _MENU_ coupons'),
                            sSearch: ''
                        },
                        order: [[0, 'asc']],
                        columns: [
                            {
                                title: gettext('Name'),
                                data: 'title'
                            },
                            {
                                title: gettext('Coupon Report'),
                                data: 'id',
                                fnCreatedCell: function (nTd, sData, oData) {
                                    $(nTd).html(this.downloadTpl(oData.id));
                                },
                                orderable: false
                             }
                        ]
                    });

                    // NOTE: #couponTable_filter is generated by dataTables
                    this.$el.find('#couponTable_filter label').prepend($emptyLabel);

                    this.$el.find('#couponTable_filter input')
                        .attr('placeholder', filterPlaceholder)
                        .addClass('field-input input-text')
                        .removeClass('form-control input-sm');

                }
            },

            render: function () {
                this.$el.html(this.template);
                this.renderCouponTable();
                this.refreshTableData();
                return this;
            },

            /**
             * Refresh the data table with the collection's current information.
             */
            refreshTableData: function () {
                var data = this.collection.map(this.getRowData, this),
                    $table = this.$el.find('#couponTable').DataTable();

                $table.clear().rows.add(data).draw();
                return this;
            },

            /**
             * Download voucher report for a Coupon product
             */
            downloadVoucherReport: function (event) {
                var coupon_id = $(event.currentTarget).data('coupon-id'),
                    url = '/api/v2/vouchers/download_voucher_report/' + coupon_id;

                event.preventDefault();
                window.open(url, '_blank');
                this.refreshTableData();
                return this;
            }
        });
    }
);
