from isitopen.tests.customer.base import *

class TestFollowUpDataOpennessEnquiry(TestController):

    follow_up_data = {
        'to': u'data.controller@appropriatesoftware.net',
        'subject': u'Some follow up',
        'body': u'Dear sir, further to my enquiry...',
    }  # Todo: Follow up values.

    def test_187(self):
        """
        The system shall present to enquiry owners an option for following up data
        openness enquiries when the enquiry is viewed.
        """
        # Check there isn't an option.
        self.logout() # Not authenticated.
        res = self.get(controller='enquiry', action='view', id=self.enq_id)
        self.fail_if_checkpoint('option-to-follow-up-enquiry', res)
        self.login(credentials=self.other_credentials) # Not owner of enq_id.
        res = self.get(controller='enquiry', action='view', id=self.enq_id)
        self.fail_if_checkpoint('option-to-follow-up-enquiry', res)
        # Check there is an option.
        self.login(credentials=self.admin_credentials) # Is admin.
        res = self.get(controller='enquiry', action='view', id=self.enq_id)
        self.assert_checkpoint('option-to-follow-up-enquiry', res)
        self.login(credentials=self.tester_credentials) # Is owner of enq_id.
        res = self.get(controller='enquiry', action='view', id=self.enq_id)
        self.assert_checkpoint('option-to-follow-up-enquiry', res)
        # Todo: Test the link works.
    
    def test_235(self):
        """
        The system shall present to owners of a data openness enquiry a form for following up the enquiry.
        """
        # Check there isn't a form.
        self.logout() # Not authenticated.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.fail_if_checkpoint('form-for-follow-up-enquiry', res)
        self.login(credentials=self.other_credentials) # Not owner of enq_id.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.fail_if_checkpoint('form-for-follow-up-enquiry', res)
        # Check there is a form.
        self.login(credentials=self.tester_credentials) # Is owner of enq_id.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.assert_form_for_follow_up_enquiry(res)
        self.login(credentials=self.admin_credentials) # Is admin.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.assert_form_for_follow_up_enquiry(res)
        follow_up_form = res.forms[0]
        # Read form field values.
        to = follow_up_form['to'].value
        subject = follow_up_form['subject'].value
        body = follow_up_form['body'].value
        assert to
        assert subject
        assert body
        enquiry = model.Enquiry.query.get(self.enq_id)
        original = enquiry.messages[0]
        assert (original.to in to), "Can't see '%s' in to '%s'." % (original.to, to)
        assert (original.subject in subject), "Can't see '%s' in subject '%s'." % (original.subject, subject)
        assert (" wrote:" in body), "Can't see ' wrote:' in body '%s'." % body
       
    def test_189(self):
        """
        The system shall accept submissions from data openness enquiry owners using the form for following up enquiries by presenting the follow up summary and prompting for confirmation.
        """
        self.login(credentials=self.tester_credentials) # Is owner of enq_id.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.assert_form_for_follow_up_enquiry(res)
        res = self.submit(res=res, form_data=self.follow_up_data, button_name='followup')
        self.assert_form_for_confirm_follow_up(res)
        enquiry = model.Enquiry.query.get(self.enq_id)
        follow_up_form = res.forms[0]
        print follow_up_form.fields['to'][0].value
        # Read hidden form field values.
        to = follow_up_form.fields['to'][0].value
        subject = follow_up_form.fields['subject'][0].value
        body = follow_up_form.fields['body'][0].value
        assert to
        assert subject
        assert body
        assert (self.follow_up_data['to'] in to), "Can't see '%s' in to '%s'." % (self.follow_up_data['to'], to)
        assert (self.follow_up_data['subject'] in subject), "Can't see '%s' in subject '%s'." % (self.follow_up_data['subject'], subject)
        assert (self.follow_up_data['body'] in body), "Can't see '%s' in subject '%s'." % (self.follow_up_data['body'], body)
        # Todo: Test for admin, other, and unauthenticated users.
 
    def test_190(self):
        """
        The system shall accept from data openness enquiry owners confirmation of the enquiry follow up by creating a pending message to a data handler and indicating to the user that this has happened.
        """
        self.login(credentials=self.tester_credentials) # Is owner of enq_id.
        res = self.get(controller='enquiry', action='followup', id=self.enq_id)
        self.assert_form_for_follow_up_enquiry(res)
        res = self.submit(res=res, form_data=self.follow_up_data, button_name='followup')
        self.assert_form_for_confirm_follow_up(res)
        res = self.submit(res=res, button_name='confirm')
        # Assert confirmation has been received.
        self.assert_indicator_for_confirmed_follow_up(res)
        # Assert message created properly.
        login = self.tester_credentials['login']
        message = model.Message.query.filter_by(sender=login).first()
        assert message, str(model.Message.query.all())
        assert self.follow_up_data['subject'] == message.subject, (self.follow_up_data['subject'], message.subject)
        return
        assert self.follow_up_data['body'] in message.mimetext, (self.follow_up_data['body'], message.mimetext)
        #assert 'Sent by' in message.mimetext
        assert login == message.enquiry.owner.email
        # Todo: Test for admin, other, and unauthenticated users.

