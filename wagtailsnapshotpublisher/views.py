import json

from django.apps import apps
from django.forms.models import model_to_dict
from django.forms.models import modelform_factory
from django.http import HttpResponse, JsonResponse, HttpResponseServerError, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from wagtail.core.models import Page, PageRevision

from djangosnapshotpublisher.publisher_api import PublisherAPI

from .models import WSSPContentRelease, document_load_dynamic_elements
from .forms import PublishReleaseForm, FrozenReleasesForm
from .utils import get_dynamic_element_keys


def get_content_details(site_code, release_uuid, content_type, content_key):
    publisher_api = PublisherAPI()
    try:
        content_release = None
        if release_uuid:
            # get ContentRelease
            content_release = WSSPContentRelease.objects.get(
                site_code=site_code,
                uuid=release_uuid,
            )
        else:
            # get live ContentRelease
            response = publisher_api.get_live_content_release(release.site_code)
            if response['status'] == 'error':
                return response
            else:
                release_id = response['content']
                content_release = WSSPContentRelease.objects.get(id=release_id)
    except WSSPContentRelease.DoesNotExist:
        pass
    
    response = publisher_api.get_document_from_content_release(
        site_code,
        release_uuid,
        content_key,
        content_type,
    )

    if response['status'] == 'success':
        data = json.loads(response['content'].document_json)
        dynamic_element_keys = get_dynamic_element_keys(data)
        if dynamic_element_keys and len(dynamic_element_keys) > 0:
            data.update({
                'dynamic_element_keys': dynamic_element_keys,
            })
            data, updated = document_load_dynamic_elements(content_release, data)
    else:
        return response

    return data


def unpublish_page(request, page_id, release_id, recursively=False):
    page = get_object_or_404(Page, id=page_id).specific
    page.unpublish_or_delete_from_release(release_id, recursively)
    return redirect('wagtailadmin_explore', page.get_parent().id)


def unpublish_recursively_page(request, page_id, release_id):
    return unpublish_page(request, page_id, release_id, True)


def unpublish(request, content_app, content_class, content_id, release_id):
    model_class = apps.get_model(content_app, content_class)
    instance = get_object_or_404(model_class, id=content_id)
    instance.unpublish_or_delete_from_release(release_id)
    return redirect('/admin/{}/{}/'.format(content_app, content_class))


def remove_page(request, page_id, release_id, recursively=False):
    page = get_object_or_404(Page, id=page_id).specific
    page.unpublish_or_delete_from_release(release_id, recursively, True)
    return redirect('wagtailadmin_explore', page.get_parent().id)


def remove_recursively_page(request, page_id, release_id):
    return remove_page(request, page_id, release_id, True)


def remove(request, content_app, content_class, content_id, release_id):
    model_class = apps.get_model(content_app, content_class)
    instance = get_object_or_404(model_class, id=content_id)
    instance.unpublish_or_delete_from_release(release_id, False, True)
    return redirect('/admin/{}/{}/'.format(content_app, content_class))


def preview_model(request, content_app, content_class, content_id, preview_mode='default', load_dynamic_element=True):
    model_class = apps.get_model(content_app, content_class)
    form_class = modelform_factory(model_class, fields=[field.name for field in model_class._meta.get_fields()])
    form = form_class(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        serializers = instance.get_serializers()
        serialized_page = serializers[preview_mode]['class'](instance=instance)
        data = serialized_page.data
        if load_dynamic_element:
            dynamic_element_keys = get_dynamic_element_keys(data)
            if dynamic_element_keys and len(dynamic_element_keys) > 0:
                data.update({
                    'dynamic_element_keys': dynamic_element_keys,
                })
                data, updated = document_load_dynamic_elements(instance.live_releave, data)
        return JsonResponse(data)
    else:
        print(form.errors)
        return HttpResponseServerError('Form is not valid')


def preview_instance(request, content_app, content_class, content_id, preview_mode='default', load_dynamic_element=True):
    model_class = apps.get_model(content_app, content_class)
    instance = model_class.objects.get(id=content_id)

    serializers = instance.get_serializers()
    serialized_page = serializers[preview_mode]['class'](instance=instance)
    data = serialized_page.data
    if load_dynamic_element:
        dynamic_element_keys = get_dynamic_element_keys(data)
        if dynamic_element_keys and len(dynamic_element_keys) > 0:
            data.update({
                'dynamic_element_keys': dynamic_element_keys,
            })
            data, updated = document_load_dynamic_elements(instance.live_releave, data)
    return JsonResponse(data)


def release_detail(request, release_id, set_live_button=False, release_id_to_compare_to=None):
    publisher_api = PublisherAPI()
    release = WSSPContentRelease.objects.get(id=release_id)

    publish_release_form = PublishReleaseForm()
    frozen_releases_form = FrozenReleasesForm(release.site_code)

    if request.method == 'POST' and release_id_to_compare_to is None:
        frozen_releases_form = FrozenReleasesForm(release.site_code, request.POST)
        if frozen_releases_form.is_valid():
            # redirect to compare with this release
            release_id_to_compare_to = frozen_releases_form.cleaned_data['releases']
            return release_detail(request, release_id, set_live_button, release_id_to_compare_to.id)

    if request.method == 'POST' and release_id_to_compare_to is None:
        publish_release_form = PublishReleaseForm(request.POST)
        if publish_release_form.is_valid():
            publish_type = publish_release_form.cleaned_data['publish_type']
            publish_datetime = publish_release_form.cleaned_data['publish_datetime']

            if publish_datetime:
                publish_datetime = publish_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')

            return release_set_live(request, release_id, publish_datetime)


    if frozen_releases_form.fields['releases'].queryset is None or not frozen_releases_form.fields['releases'].queryset.exists():
        frozen_releases_form = None

    # get current live release
    compare_with_live = True
    response = publisher_api.get_live_content_release(release.site_code)
    if response['status'] == 'error':
        return render(request, 'wagtailadmin/release/detail.html', {
            'set_live_button': set_live_button,
            'release': release,
            'error_msg': response['error_msg'],
            'publish_release_form': publish_release_form,
        })
    release_to_compare_to = response['content']

    if release_id_to_compare_to and release_to_compare_to.id != release_id_to_compare_to:
        compare_with_live = False
        release_to_compare_to = WSSPContentRelease.objects.get(pk=release_id_to_compare_to)

    response = publisher_api.compare_content_releases(release.site_code, release.uuid, release_to_compare_to.uuid)
    comparison = response['content']

    added_pages = []
    removed_pages = []
    changed_pages = []
    extra_contents = []
    for item  in comparison:
        if item['content_type'] == 'page':
            if item['diff'] == 'Added':
                page_revision = PageRevision.objects.get(id=item['parameters']['revision_id'])
                item['page_revision'] = page_revision
                item['title'] = json.loads(page_revision.content_json)['title']
                added_pages.append(item)
            if item['diff'] == 'Removed':
                page_revision = PageRevision.objects.get(id=item['parameters']['revision_id'])
                item['title'] = json.loads(page_revision.content_json)['title']
                item['page_revision'] = page_revision
                removed_pages.append(item)
            if item['diff'] == 'Changed' and 'revision_id' in item['parameters']['release_from']:
                page_revision = PageRevision.objects.get(id=item['parameters']['release_from']['revision_id'])
                item['page_revision_from'] = page_revision
                item['page_revision_compare_to'] = PageRevision.objects.get(id=item['parameters']['release_compare_to']['revision_id'])
                item['title'] = json.loads(page_revision.content_json)['title']
                changed_pages.append(item)
        else:
            extra_contents.append(item)

    return render(request, 'wagtailadmin/release/detail.html', {
        'comparison': comparison,
        'added_pages': added_pages,
        'changed_pages': changed_pages,
        'removed_pages': removed_pages,
        'extra_contents': json.dumps(extra_contents, indent=4) if extra_contents and request.user.has_perm('wagtailadmin.access_dev') else None,
        'set_live_button': set_live_button,
        'release': release,
        'release_to_compare_to': release_to_compare_to,
        'publish_release_form': publish_release_form,
        'frozen_releases_form': frozen_releases_form,
        'compare_with_live': compare_with_live,
    })


def release_set_live_detail(request, release_id):
    return release_detail(request, release_id, set_live_button=True)


def release_set_live(request, release_id, publish_date=None):
    publisher_api = PublisherAPI()
    release = WSSPContentRelease.objects.get(id=release_id)
    if publish_date:
        publisher_api.freeze_content_release(release.site_code, release.uuid, publish_date)
    else:
        publisher_api.set_live_content_release(release.site_code, release.uuid)
    WSSPContentRelease.objects.live(
        site_code=release.site_code,
    )
    return redirect('/admin/{}/{}/'.format('wagtailsnapshotpublisher', 'wsspcontentrelease'))


def release_archive(request, release_id):
    publisher_api = PublisherAPI()
    release = WSSPContentRelease.objects.get(id=release_id)
    publisher_api.archive_content_release(release.site_code, release.uuid)
    return redirect('/admin/{}/{}/'.format('wagtailsnapshotpublisher', 'wsspcontentrelease'))


def get_document_release(
        request, site_code, content_release_uuid=None, content_type='content', content_key=None):
    return JsonResponse(
        get_content_details(site_code, content_release_uuid, content_type, content_key)
    )


def release_restore(request, release_id):
    try:
        release_to_restore = WSSPContentRelease.objects.get(id=release_id)
        site_code = release_to_restore.site_code
        live_release = WSSPContentRelease.objects.live(site_code=site_code)

        WSSPContentRelease.objects.lives(
            site_code=site_code,
        ).exclude(
            pk=live_release.pk,
        ).get(
            pk=release_to_restore.pk,
        )
    except WSSPContentRelease.DoesNotExist:
        raise Http404(_('This release cannot be restore'))
    
    title = release_to_restore.title
    if not release_to_restore.restored:
        title = '{} - Restored'.format(release_to_restore.title)

    release = WSSPContentRelease(
        version_type=0,
        title=title,
        site_code=site_code,
        base_release=release_to_restore,
        restored=True,
    )
    release.save()

    return release_set_live(request, release.id)


def release_unfreeze(request, release_id):
    try:
        release_to_restore = WSSPContentRelease.objects.get(id=release_id)
        release_to_restore.status = 0
        release_to_restore.publish_datetime = None
        release_to_restore.save()
    except WSSPContentRelease.DoesNotExist:
        raise Http404(_('This release cannot be restore'))
    
    return redirect('/admin/{}/{}/'.format('wagtailsnapshotpublisher', 'wsspcontentrelease'))
