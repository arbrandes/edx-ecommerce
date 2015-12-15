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

            function visible(selector) {
                return !view.$el.find(selector).closest('.form-group').hasClass('hidden');
            }

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

            describe('enrollment code', function () {
                beforeEach(function () {
                    view.$el.find('[name=code_type]').val('enrollment').trigger('change');
                });

                it('should show the price field', function () {
                    expect(visible('[name=price]')).toBe(true);
                });

                it('should hide discount and code fields', function () {
                    expect(visible('[name=benefit_value]')).toBe(false);
                    expect(visible('[name=code]')).toBe(false);
                });

                it('should show the quantity field only for single-use vouchers', function () {
                    view.$el.find('[name=voucher_type]').val('Single use').trigger('change');
                    expect(visible('[name=quantity]')).toBe(true);
                    view.$el.find('[name=voucher_type]').val('Multi-use').trigger('change');
                    expect(visible('[name=quantity]')).toBe(false);
                    view.$el.find('[name=voucher_type]').val('Once per customer').trigger('change');
                    expect(visible('[name=quantity]')).toBe(false);
                });
            });

            describe('discount', function () {
                beforeEach(function () {
                    view.$el.find('[name=code_type]').val('discount').trigger('change');
                });

                it('should show the discount field', function () {
                    expect(visible('[name=benefit_value]')).toBe(true);
                });

                it('should hide the price field', function () {
                    expect(visible('[name=price]')).toBe(false);
                });

                it('should indicate the benefit type', function () {
                    view.$el.find('[name=code_type]').val('enrollment').trigger('change');
                    expect(view.$el.find('.benefit-addon').html()).toBe('%');
                    view.$el.find('[name=benefit_type]').val('Fixed').trigger('change');
                    expect(view.$el.find('.benefit-addon').html()).toBe('$');
                });

                it('should show the code field only for multi-use vouchers', function () {
                    view.$el.find('[name=voucher_type]').val('Single use').trigger('change');
                    expect(visible('[name=code]')).toBe(false);
                    view.$el.find('[name=voucher_type]').val('Multi-use').trigger('change');
                    expect(visible('[name=code]')).toBe(true);
                    view.$el.find('[name=voucher_type]').val('Once per customer').trigger('change');
                    expect(visible('[name=code]')).toBe(true);
                });
            });

        });
    }
);
