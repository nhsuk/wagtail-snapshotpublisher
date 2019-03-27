from django.core.serializers.json import DjangoJSONEncoder


class StreamFieldEncoder(DjangoJSONEncoder):
    def default(self, obj):
        from wagtail.core.blocks.stream_block import StreamValue
        if isinstance(obj, StreamValue):
            new_obj = obj.get_prep_value()
            for item in new_obj:
                try:
                    fields_to_store = obj.stream_block.child_blocks[item['type']].fields_to_store
                    item['value'] = {key: val for key, val in item['value'].items() if key in fields_to_store}
                except AttributeError:
                    pass
            return new_obj
        return super(StreamFieldEncoder, self).default(obj)