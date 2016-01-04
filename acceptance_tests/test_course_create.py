"""
Ecommerece Course create about page (with registration button)
"""

from acceptance_tests.pages import EcommerceAppPage
from bok_choy.promise import EmptyPromise



class CreateCoursePage(EcommerceAppPage):
    path = "courses/new"

    def is_browser_on_page(self):
        return self.browser.title.startswith('Create New Course')

    def select_course_type(self):
        EmptyPromise(lambda: self.q(css='.course-seat.empty').visible, "Select Course Type visible").fulfill()



