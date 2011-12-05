from donelist.tests import *

class TestFormsController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='forms'))
        # Test response...
