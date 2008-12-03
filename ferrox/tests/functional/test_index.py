from ferrox.tests import *

class TestIndexController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='index'))
        # Test response...
