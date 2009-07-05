from isitopen.lib.gmail import Gmail
from isitopen.lib import mailer
import isitopen.model as model

ISITOPEN_HEADER_ID = 'X-IsItOpen-Message-Id'

def send_pending():
    '''Send pending messages.'''
    pending = model.Message.query.filter_by(
            status=model.MessageStatus.not_yet_sent
            ).all()
    results = []
    m = mailer.Mailer.default()
    for message in pending:
        try:
            e = message.email
            e[ISITOPEN_HEADER_ID] = m.id
            if e.sender:
                # use bcc to ensure recipient replies to isitopen not sender
                e['bcc'] = e.sender
            m.send(message.email)
            message.status = model.MessageStatus.sent_not_synced
            model.Session.commit()
            results.append([message.id, message.status])
        except Exception, inst:
            results.append('ERROR: %s' % inst)
    return results

def sync_sent_mail():
    '''Sync up sent emails with their L{Message}s.'''
    tosync = model.Message.query.filter_by(
            status=model.MessageStatus.sent_not_synced
            ).all()
    results = []
    g = Gmail.default()
    for message in tosync:
        try:
            emailobj = g.search_sent_by_header(ISITOPEN_HEADER_ID, m.id)
            message.mimetext = emailobj.as_string()
            message.status = model.MessageStatus.sent
            model.Session.commit()
            results.append([message.id, message.status])
        except Exception, inst:
            results.append('ERROR: %s' % inst)
    return results


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
