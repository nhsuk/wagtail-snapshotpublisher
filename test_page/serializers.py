from rest_framework import serializers

from wagtail.api.v2.serializers import StreamField

from .models import TestPage, TestModel


class TestPageSerializer(serializers.ModelSerializer):
    body = StreamField()

    class Meta:
        model = TestPage
        fields = (
            'title',
            'name1',
            'body',
            'test_related_model',
        )


class TestPageCoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestPage
        fields = (
            'title',
            'name1',
        )


class TestModelSerializer(serializers.ModelSerializer):
    body = StreamField()

    def to_representation(self, data):
        serialized_data = super(TestModelSerializer, self).to_representation(data)
        serialized_data['redirects'] = data.get_redirections()
        return serialized_data

    class Meta:
        model = TestModel
        fields = (
            'name1',
            'name2',
            'body',
            'content_release',
        )


class TestModelCoverSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestModel
        fields = (
            'name1',
        )
