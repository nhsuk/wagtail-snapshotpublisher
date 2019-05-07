import json

from bs4 import BeautifulSoup

from django.core.serializers.json import DjangoJSONEncoder

from wagtail.core.blocks.struct_block import StructValue
from wagtail.core.blocks.stream_block import StreamValue
from wagtail.core.rich_text import expand_db_html


class StreamFieldEncoder(DjangoJSONEncoder):

    def default(self, obj):
        from wagtail.core.blocks.stream_block import StreamValue
        if isinstance(obj, StreamValue):
            new_obj = obj.get_prep_value()
            for item in new_obj:
                try:
                    return recursive_get_data(enumerate(obj.stream_data))
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
            elif type(val) == str and bool(BeautifulSoup(val, "html.parser").find()):
                val = expand_db_html(val)
            values.update({
                key: val
            })
        return values


def recursive_get_data(stream_data_item):
    data = []
    for key, item in stream_data_item:
        if type(item) == dict:
            data.append(item)
        else:
            values = {}
            for item2 in item:
                if type(item2) == StructValue:
                    for i, (key2, value2) in enumerate(item2.items()):
                        if type(value2) == StreamValue:
                            values.update(
                                {
                                    key2: recursive_get_data(enumerate(value2.stream_data))
                                }
                            )
                        else:
                            try:
                                print(key2)
                                values.update({
                                    key2: value2.block.get_api_representation(value2)
                                })
                            except:
                                if bool(BeautifulSoup(str(value2), "html.parser").find()):
                                    value2 = expand_db_html(value2.source)
                                values.update({
                                    key2: str(value2),
                                })

            data.append({
                'type': item[0],
                'value': values,
                'id': item[-1],
            })

    return data
