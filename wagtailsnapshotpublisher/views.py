import json

from django.apps import apps
from django.forms.models import model_to_dict
from django.forms.models import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render

from wagtail.core.models import Page, PageRevision

from wagtailsnapshotpublisher.models import WSSPContentRelease
from djangosnapshotpublisher.publisher_api import PublisherAPI


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


def preview_model(request, content_app, content_class, content_id):
    model_class = apps.get_model(content_app, content_class)
    form_class = modelform_factory(model_class, fields=[field.name for field in model_class._meta.get_fields()])
    form = form_class(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)
        object_dict = model_class.document_parser(instance, model_class.structure_to_store, model_to_dict(instance))
        return JsonResponse(object_dict)
    else:
        return HttpResponseServerError('Form is not valid')


def release_detail(request, release_id, set_live_button=False):
    publisher_api = PublisherAPI()
    release = WSSPContentRelease.objects.get(id=release_id)
    response = publisher_api.get_live_content_release(release.site_code)
    live_release = response['content']
    response = publisher_api.compare_content_releases(release.site_code, release.uuid, live_release.uuid)
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
            if item['diff'] == 'Changed':
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
        'live_release': live_release,
        # 'error_msg': error_msg,
    })


def release_set_live_detail(request, release_id):
    return release_detail(request, release_id, set_live_button=True)


def release_set_live(request, release_id):
    publisher_api = PublisherAPI()
    release = WSSPContentRelease.objects.get(id=release_id)
    publisher_api.set_live_content_release(release.site_code, release.uuid)
    return redirect('/admin/{}/{}/'.format('wagtailsnapshotpublisher', 'wsspcontentrelease'))


def get_document_release(
        request, site_code, content_release_uuid=None, type='site_definition', key='site_definition'):

    publisher_api = PublisherAPI()

    if not content_release_uuid:
        reponse = publisher_api.get_live_content_release(site_code)
        if reponse['status'] != 'success':
            return JsonResponse(reponse)
        content_release_uuid = reponse['content'].uuid

    reponse = publisher_api.get_document_from_content_release(
        site_code,
        content_release_uuid,
        key,
        type,
    )

    if reponse['status'] == 'success':
        return HttpResponse(reponse['content'].document_json, content_type="application/json")
    return JsonResponse(reponse)
