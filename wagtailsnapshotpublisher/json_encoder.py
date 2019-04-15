import json

from bs4 import BeautifulSoup

from django.core.serializers.json import DjangoJSONEncoder

from wagtail.core.rich_text import expand_db_html


class StreamFieldEncoder(DjangoJSONEncoder):

    def default(self, obj):
        from wagtail.core.blocks.stream_block import StreamValue
        if isinstance(obj, StreamValue):
            new_obj = obj.get_prep_value()
            for item in new_obj:
                try:
                    fields_to_store = obj.stream_block.child_blocks[item['type']].fields_to_store
                    values = self.dict_parse_html(item['value'])
                    item['value'] = values
                except AttributeError:
                    pass
            return new_obj
        return super(StreamFieldEncoder, self).default(obj)

    def dict_parse_html(self, items):
        values = {}
        for key, val in items.items():
            if type(val) == list:
                new_val = []
                for item in val:
                    new_val.append(self.dict_parse_html(item))
                val = new_val
            elif type(val) == dict:
                val = self.dict_parse_html(val)
            elif bool(BeautifulSoup(val, "html.parser").find()):
                val = expand_db_html(val)
            values.update({
                key: val
            })
        return values
