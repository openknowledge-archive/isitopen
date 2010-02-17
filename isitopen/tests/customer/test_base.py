from isitopen.tests.customer.base import *

class TestTestController(TestController):

    def test__find_last_pending_action_id(self):
        import time
        for i in range(0,5):
            pending_action = model.PendingAction()
            model.Session.commit()
        last_id = self._find_last_pending_action_id()
        assert pending_action.id == last_id, "Not equal: %s != %s" % (
            pending_action.id, last_id
        )

