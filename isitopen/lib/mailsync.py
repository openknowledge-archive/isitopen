import logging

from isitopen.lib.gmail import Gmail
from isitopen.lib import mailer
import isitopen.model as model

log = logging.getLogger(__name__)

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
def check_for_responses(mailbox=None):
    g = Gmail.default()
    results = []
    msgs_dict = g.unread(mailbox)
    # log.debug('check_for_responses: no. of items = %s' % len(msgs_dict))
    for mboxid, message in msgs_dict.items():
        # log.debug('check_for_responses: %s, %s, %s' % (mboxid, message['from'],
        #    message['subject']) )
        # ignore bounces ....
        if 'From' in message and 'mailer-daemon@googlemail.com' in message['From']:
            results.append([message['Message-Id'], 'Skip: looks like bounce'])
            continue
        try:
            # TODO: extract timestamp etc
            enquiry = finder.enquiry_for_message(message)
            if not enquiry:
                results.append([message['Message-Id'], 'Skip: found no related enquiry'])
                continue

            m = model.Message(
                status=model.MessageStatus.response_no_notification,
                enquiry=enquiry,
                mimetext = message.as_string()
                )
            model.Session.commit()
            results.append([message['Message-Id'], 'Synced', m.id])
            g.mark_read(mboxid)
            # g.gmail_label(message, 'enquiry/' + m.enquiry.id) # get message from imap via MIME Message-Id, copy to "enquiry/<enq_id>"
        except Exception, inst:
            results.append([message['Message-Id'], 'ERROR: %s' % inst])
    return results

from pylons import config
import isitopen.lib.helpers as h
import email as E
def _make_response_email(enquiry):
    default_from = config['enquiry.from']
    body = '''Hi,

You have received a response to your enquiry "%s" [%s]

Here's a link to your enquiry where you can respond:

<%s>

The Is It Open Team
''' % ( enquiry.summary, enquiry.id,
        'http://isitopen.ckan.net%s' % h.url_for(controller='enquiry', action='read', id=enquiry.id)
        )
    ourmail = E.message_from_string(body)
    ourmail['To'] = enquiry.owner.email
    # TODO: use a no-reply address ...
    ourmail['From'] = ourmail['Reply-To'] = default_from
    ourmail['Subject'] = '[isitopen]: Response to your enquiry "%s" [%s]' % (
            enquiry.summary, enquiry.id)
    return ourmail

def send_response_notifications():
    '''Send notifications of responses.'''
    pending = model.Message.query.filter_by(
            status=model.MessageStatus.response_no_notification
            ).all()
    results = []
    ourmailer = mailer.Mailer.default()
    for message in pending:
        try:
            enq = message.enquiry
            if not enq.owner or not enq.owner.email:
                continue

            email = _make_response_email(enq)
            ourmailer.send(email)
            message.status = model.MessageStatus.response
            model.Session.commit()
            
            results.append([message.id, message.status])
        except Exception, inst:
            results.append('ERROR: %s' % inst)
    return results

