import re

import isitopen.model as model

class Finder(object):
    subject_regex = re.compile('.*\[iio-(\d+)\]')
    
    def extract_id_from_subject(self, subject):
        matches = self.subject_regex.findall(subject)
        if matches:
            return int(matches[0])

    def enquiry_for_message(self, message):
        # first check in-reply-to and references headers
        # may in future move to subject based matching
        inreplyto = message['In-Reply-To']
        references = message['References']
        lastref = None
        if references:
            lastref = '<' + references.split('<')[-1]
        for msgid in [ inreplyto, lastref ]:
            # may be more efficient to query gmail for this ...
            if msgid:
                msgid_field = 'Message-ID: %s' % msgid
                msg = model.Message.query.filter(
                    model.Message.mimetext.ilike('%' + msgid_field + '%')
                    ).first()
                if msg:
                    return msg.enquiry

