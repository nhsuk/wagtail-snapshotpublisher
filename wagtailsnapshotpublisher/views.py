from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect

from wagtail.core.models import Page

from djangosnapshotpublisher.publisher_api import PublisherAPI


def unpublish_page(request, page_id, release_id):
    page = get_object_or_404(Page, id=page_id).specific

    page.unpublish_from_release(release_id)

    return redirect('wagtailadmin_explore', page.get_parent().id)


def unpublish(request, content_app, content_class, content_id, release_id):
    model_class = apps.get_model(content_app, content_class)
    instance = get_object_or_404(model_class, id=content_id)

    instance.unpublish_from_release(release_id)

    return redirect('/admin/{}/{}/'.format(content_app, content_class))


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
