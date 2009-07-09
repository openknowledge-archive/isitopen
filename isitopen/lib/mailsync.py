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
    ourmailer = mailer.Mailer.default()
    for message in pending:
        try:
            e = message.email
            e[ISITOPEN_HEADER_ID] = message.id
            if message.sender:
                # use bcc to ensure recipient replies to isitopen not sender
                e['Bcc'] = message.sender
                
            ourmailer.send(message.email)
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
            # TODO: improve this (we cannot go through all sent messages every
            # time)
            # searching with an X-* header does *not* work ...
            # so have to do this by hand (not good ...)
            emails = g.messages_for_mailbox(g.sent,
                    # '(%s "%s")' % (ISITOPEN_HEADER_ID, message.id)
                )
            # should only be one 
            # assert len(emails) == 1, 'Should have one (+ only one) matching email'
            # emailobj = emails[emails.keys()[0]]
            for emailobj in emails.values():
                if emailobj[ISITOPEN_HEADER_ID] == message.id:
                    message.mimetext = emailobj.as_string()
                    message.status = model.MessageStatus.sent
                    model.Session.commit()
            results.append([message.id, message.status])
        except Exception, inst:
            results.append([message.id, 'ERROR: %s' % inst])
            # during testing
            # raise
    return results


import isitopen.lib.finder
finder = isitopen.lib.finder.Finder()
def check_for_responses(folder=None):
    g = Gmail.default()
    # unread items in the inbox
    results = []
    for mboxid, message in g.unread(folder).items():
        # ignore bounces ....
        if 'From' in message and 'mailer-daemon@googlemail.com' in message['From']:
            results.append([message, 'Skipping as looks like bounce'])
            continue
        try:
            # TODO: extract timestamp etc
            m = model.Message(status=model.MessageStatus.response)
            m.mimetext = message.as_string()
            m.enquiry = finder.enquiry_for_message(message)
            model.Session.commit()
            g.mark_read(mboxid)
            results.append([message, 'Synced'])
            # g.gmail_label(message, 'enquiry/' + m.enquiry.id) # get message from imap via MIME Message-Id, copy to "enquiry/<enq_id>"
        except Exception, inst:
            results.append([message, 'ERROR: %s' % inst])
    return results


