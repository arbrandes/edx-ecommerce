define([
        'jquery',
        'views/coupon_create_edit_view',
        'views/alert_view',
        'models/coupon_model'
    ],
    function ($,
              CouponCreateEditView,
              AlertView,
              Coupon) {
        'use strict';

        describe('coupon create view', function () {
            var view,
                model;

            beforeEach(function () {
                model = new Coupon();
                view = new CouponCreateEditView({ model: model, editing: false }).render();
            });

            it('should throw an error if submitted with blank fields', function () {
                var errorHTML = '<strong>Error!</strong> Please complete all required fields.';
                view.formView.submit($.Event('click'));
                expect(view.$el.find('.alert').length).toBe(1);
                expect(view.$el.find('.alert').html()).toBe(errorHTML);
            });

        });
    }
);
