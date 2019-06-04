"""
.. module:: wagtailsnapshotpublisher.forms
"""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from wagtail.admin.widgets import AdminDateTimeInput

from .models import WSSPContentRelease


class PublishReleaseForm(forms.Form):
    """ PublishReleaseForm """
    PUBLISH_TYPE = (
        ('now', 'Now'),
        ('schedule_date', 'Schedule a publish date'),
    )
    publish_type = forms.ChoiceField(choices=PUBLISH_TYPE, widget=forms.RadioSelect, initial='now')
    publish_datetime = forms.DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        """ __init__ """
        super().__init__(*args, **kwargs)
        self.fields['publish_datetime'].widget = AdminDateTimeInput()

    def clean_publish_datetime(self):
        """ clean_publish_datetime """
        publish_datetime = self.cleaned_data['publish_datetime']
        if publish_datetime and publish_datetime < timezone.now():
            raise forms.ValidationError(_('Publish Datetime must be in the future'),
                                        code='publish_datetime_in_future')

        return publish_datetime


class FrozenReleasesForm(forms.Form):
    """ FrozenReleasesForm """
    releases = forms.ModelChoiceField(queryset=None)

    def __init__(self, site_code, *args, **kwargs):
        """ __init__ """
        super().__init__(*args, **kwargs)
        publish_datetime = timezone.now()
        live_release = WSSPContentRelease.objects.live(site_code=site_code)

        # get releases
        self.fields['releases'].queryset = WSSPContentRelease.objects.filter(
            site_code=site_code,
            # publish_datetime__gte=live_release_publish_datetime,
            status=1,
        ).exclude(
            publish_datetime=None,
        ).order_by('publish_datetime', 'title')

        # get live_release  publish_datetime
        # live_release_publish_datetime = None
        if live_release:
            self.fields['releases'].queryset = self.fields['releases'].queryset.filter(
                publish_datetime__gte=live_release.publish_datetime,
            )
            # live_release_publish_datetime = live_release.publish_datetime

        # if only live release ignore it as it become the default comparaison
        if live_release and self.fields['releases'].queryset.count() == 1:
            self.fields['releases'].queryset = None
