define([
        'jquery',
        'backbone',
        'underscore',
        'underscore.string',
        'moment',
        'text!templates/coupon_detail.html'
    ],
    function ($,
              Backbone,
              _,
              _s,
              moment,
              CouponDetailTemplate) {
        'use strict';

        return Backbone.View.extend({
            className: 'coupon-detail-view',

            initialize: function () {
                this.listenTo(this.model, 'change', this.render);
            },

            codeStatus: function(voucher) {
                var endDate = moment(new Date(voucher.end_datetime));
                return (endDate.isAfter(Date.now())) ? 'ACTIVE':'INACTIVE';
            },

            couponType: function(voucher) {
                var benefitType = voucher.benefit[0],
                    benefitValue = voucher.benefit[1];
                return (benefitType === 'Percentage' && benefitValue === 100) ? 'Enrollment Code':'Discount Code';
            },

            discountValue: function(voucher) {
                var benefitType = voucher.benefit[0],
                    benefitValue = voucher.benefit[1];

                return (benefitType === 'Percentage') ? benefitValue + '%':benefitValue;
            },

            formatDateTime: function(dateTime) {
                return moment(dateTime).format('MMMM DD, YYYY, h:mm A');
            },

            usageLimitation: function(voucher) {
                if (voucher.usage === 'Single use') {
                    return 'Can be used once by one customer';
                } else if (voucher.usage === 'Multi-use') {
                    return 'Can be used multiple times by multiple customers';
                } else if (voucher.usage === 'Once per customer') {
                    return 'Can only be used once per customer';
                }
                return '';
            },

            render: function () {
                var html,
                    voucher = this.model.attributes.vouchers[0];

                html = _.template(CouponDetailTemplate)({
                    coupon: this.model.attributes,
                    couponType: this.couponType(voucher),
                    codeStatus: this.codeStatus(voucher),
                    discountValue: this.discountValue(voucher),
                    course: this.model.attributes.catalog.products.attribute_values,
                    startDateTime: this.formatDateTime(voucher.start_datetime),
                    endDateTime: this.formatDateTime(voucher.end_datetime),
                    usage: this.usageLimitation(voucher),
                    price: '$' + this.model.attributes.price,
                });
                this.$el.html(html);

                this.renderVoucherTable();
                this.refreshTableData();
            },

            renderVoucherTable: function () {
                if (!$.fn.dataTable.isDataTable('#vouchersTable')) {
                    this.$el.find('#vouchersTable').DataTable({
                        autoWidth: false,
                        info: true,
                        paging: false,
                        order: [[0, 'asc']],
                        searching: false,
                        columns: [
                            {
                                title: gettext('Code'),
                                data: 'code'
                            },
                            {
                                title: gettext('Status'),
                                data: ''
                            }
                        ]
                    });
                }
            },

            refreshTableData: function () {
                var data = this.model.attributes.vouchers,
                    $table = this.$el.find('#vouchersTable').DataTable();

                $table.clear().rows.add(data).draw();
                return this;
            },

            downloadVoucherReport: function (event) {
                var url = '/api/v2/vouchers/download_voucher_report/' + this.model.attributes.id;

                event.preventDefault();
                window.open(url, '_blank');
                return this;
            }
        });
    }
);
