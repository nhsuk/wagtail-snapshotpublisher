Wagtail - Snapshot Publisher
=============================

Wagtail Appplication API to store and get Document for a release using djangosnapshotpublisher package.


Quick start
-----------

1. Add "wagtailsnapshotpublisher" to your INSTALLED_APPS setting like this:

```python
INSTALLED_APPS = [
    'wagtailsnapshotpublisher',
    ...
]
```

2. Run `python manage.py migrate` to create the djangosnapshotpublisher models.

3. Setup SITE_CODE_CHOICES in setting.

```python
SITE_CODE_CHOICES = (
    ('site1', 'site1'),
    ('site2', 'site2'),
)
```

4. (Optional) To have dynamic SITE_CODE_CHOICES from a model you need to create receiver like code below where you replace `[[MODEL_CLASS]]` by your model class and `[[MODEL_ATTR_NAME]]` by the attribute name that will be use for the site_code
```python
@receiver(post_save, sender=[[MODEL_CLASS]])
@receiver(post_delete, sender=[[MODEL_CLASS]])
def update_site_code_widget_for_content_release(sender, instance, **kwargs):
    """ update_site_code_widget_for_content_release """
    from django import forms
    from wagtail.admin.edit_handlers import FieldPanel
    from wagtailsnapshotpublisher.models import WSSPContentRelease, ModelWithRelease

    site_settings = [[MODEL_CLASS]].objects.exclude(title='').values_list([[MODEL_ATTR_NAME]], [[MODEL_ATTR_NAME]])

    site_code_widget = forms.Select(
        choices=tuple([('', '---------')] + list(site_settings)),
    )

    WSSPContentRelease.get_panel_field('site_code').widget = site_code_widget
    ModelWithRelease.get_panel_field('site_code').widget = site_code_widget


try:
    update_site_code_widget_for_content_release([[MODEL_CLASS]], None)
except ProgrammingError:
    pass
```


How to use
----------

1. To add the release functionality:
    * to a wagtail page class
    ```python
        class TestPage(PageWithRelease):
            ...
            release_config = {
                'can_publish_to_release': True,
                'can_publish_to_live_release': True,
            }
            ...
    ```
    * to a model class
    ```python
        class TestModel(ModelWithRelease):
            ...
            release_config = {
                'can_publish_to_release': True,
                'can_publish_to_live_release': True,
            }
            ...
    ```
You can edit `release_config` attribute activite only the functionality that you need:
* `can_publish_to_release` to publish to a specific release
* `can_publish_to_live_release` to publish directly to the current live release

2. Define the serializers for the this class, check djangosnapshotpublisher to understand what should be the value for `[[KEY]]` and `[[TYPE]]`
```python
class TestModel(ModelWithRelease):
    ...

    def get_serializers(self):
        """ get_serializers """
        return {
            'default': {
                'key': [[KEY]],
                'type': [[TYPE]],
                'class': [[SERIALIZER_CLASS]],
            },
            ...
        }
    ...
```

[[TO DO: HOW TO USE DYNAMIC BLOCK]]

How to contribute
-----------------

### Requirements
* Docker
* docker-compose
You'll get all this lot installed nicely with (https://docs.docker.com/docker-for-mac/install).


### Setup locally
Add git hook
```
./scripts/install-hooks.sh
```
Build the image
```
docker-compose build
```
Run the containers
```
docker-compose up
```
Create super user:
```
docker-compose run --rm web python manage.py createsuperuser
```