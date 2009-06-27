from isitopen.lib.gmail import Gmail
import isitopen.model as model

def check_mail():
    g = Gmail.default()
    for mboxid, message in g.unread().items():
        print message['Subject']
        m = model.Message()
        m.mimetext = message.as_string()
        m.enquiry = _enquiry_for_message(message)
        model.Session.commit()
        # g.mark_read(message)
        # g.gmail_label(message, 'enquiry/' + m.enquiry.id) # get message from imap via MIME Message-Id, copy to "enquiry/<enq_id>"
        
def _enquiry_for_message(message):
    return model.Enquiry.query.first()