from sqlalchemy import types
try:
    import json
except ImportError:
    import simplejson as json


class JsonType(types.TypeDecorator):
    '''Store data as JSON serializing on save and unserializing on use.
    '''
    impl = types.UnicodeText

    def process_bind_param(self, value, engine):
        if value is None or value == {}:
            return None
        else:
            # ensure_ascii=False => allow unicode but still need to convert
            return unicode(json.dumps(value, ensure_ascii=False))

    def process_result_value(self, value, engine):
        # the if value part never seems to get run!!
        if value is None:
            return {}
        else:
            return json.loads(value)

    def copy(self):
        return JsonType(self.impl.length)



