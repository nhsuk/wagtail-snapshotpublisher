"""
.. module:: test_page.serializers
"""

from rest_framework import serializers

from wagtail.api.v2.serializers import StreamField

from .models import TestPage, TestModel


class TestPageSerializer(serializers.ModelSerializer):
    """ TestPageSerializer """
    body = StreamField()

    class Meta:
        """ Meta """
        model = TestPage
        fields = (
            'title',
            'name1',
            'body',
            'test_related_model',
        )


class TestPageCoverSerializer(serializers.ModelSerializer):
    """ TestPageCoverSerializer """
    class Meta:
        """ Meta """
        model = TestPage
        fields = (
            'title',
            'name1',
        )


class TestModelSerializer(serializers.ModelSerializer):
    """ TestModelSerializer """
    body = StreamField()

    def to_representation(self, instance):
        """ to_representation """
        serialized_data = super(TestModelSerializer, self).to_representation(instance)
        serialized_data['redirects'] = instance.get_redirections()
        return serialized_data

    class Meta:
        """ Meta """
        model = TestModel
        fields = (
            'name1',
            'name2',
            'body',
        )


class TestModelCoverSerializer(serializers.ModelSerializer):
    """ TestModelCoverSerializer """

    class Meta:
        """ Meta """
        model = TestModel
        fields = (
            'name1',
        )
