from django import forms
from django.utils import timezone

from wagtail.admin.widgets import AdminDateTimeInput

from .models import WSSPContentRelease


class PublishReleaseForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['publish_datetime'].widget = AdminDateTimeInput()

    PUBLISH_TYPE = (
        ('now', 'Now'),
        ('schedule_date', 'Schedule a publish date'),
    )

    publish_type = forms.ChoiceField(choices=PUBLISH_TYPE, widget=forms.RadioSelect, initial='now')
    publish_datetime = forms.DateTimeField(required=False)


    def clean_publish_datetime(self):
        publish_datetime = self.cleaned_data['publish_datetime']
        if publish_datetime and publish_datetime < timezone.now():
            raise forms.ValidationError('Publish Datetime must be in the future')            

        return publish_datetime


class FrozenReleasesForm(forms.Form):
    releases = forms.ModelChoiceField(queryset=None)

    def __init__(self, site_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        publish_datetime = timezone.now()
        live_release = WSSPContentRelease.objects.live(site_code=site_code)
        if live_release:
            publish_datetime = live_release.publish_datetime
        self.fields['releases'].queryset = WSSPContentRelease.objects.filter(
            site_code=site_code,
            publish_datetime__gte=publish_datetime,
            status=1,
        ).exclude(
            publish_datetime=None,
        )

        if live_release and self.fields['releases'].queryset.count() == 1:
            self.fields['releases'].queryset = None
