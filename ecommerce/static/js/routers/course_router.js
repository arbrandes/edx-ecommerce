define([
        'routers/page_router',
        'pages/course_list_page',
        'pages/course_detail_page',
        'pages/course_create_page',
        'pages/course_edit_page'
    ],
    function (PageRouter,
              CourseListPage,
              CourseDetailPage,
              CourseCreatePage,
              CourseEditPage) {
        'use strict';

        return PageRouter.extend({
            // Keeps track of the page/view currently on display
            currentView: null,

            // Base/root path of the app
            root: '/courses/',

            routes: {
                '(/)': 'index',
                'new(/)': 'new'
            },

            /**
             * Setup special routes.
             *
             * @param {Object} options - Data used to initialize the router. This should include a key, $el, that
             * refers to a jQuery Element where the pages will be rendered.
             */
            initialize: function (options) {
                var courseIdRegex = /([^/+]+(\/|\+)[^/+]+(\/|\+)[^/]+)/;

                // This is where views will be rendered
                this.$el = options.$el;

                // Custom routes, requiring RegExp or other complex placeholders, should be defined here
                this.route(new RegExp('^' + courseIdRegex.source + '(\/)?$'), 'show');
                this.route(new RegExp('^' + courseIdRegex.source + '/edit(\/)?$'), 'edit');

            },

            /**
             * Display a list of all courses in the system.
             */
            index: function () {
                var page = new CourseListPage();
                this.currentView = page;
                this.$el.html(page.el);
            },

            /**
             * Display details for a single course.
             * @param {String} id - ID of the course to display.
             */
            show: function (id) {
                var page = new CourseDetailPage({id: id});
                this.currentView = page;
                this.$el.html(page.el);
            },

            /**
             * Display a form for creating a new course.
             */
            new: function () {
                var page = new CourseCreatePage();
                this.currentView = page;
                this.$el.html(page.el);
            },

            edit: function (id) {
                var page = new CourseEditPage({id: id});
                this.currentView = page;
                $('#app').html(page.el);
            }
        });
    }
);
