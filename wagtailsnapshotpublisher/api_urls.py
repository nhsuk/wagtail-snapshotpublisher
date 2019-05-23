"""
.. module:: wagtailsnapshotpublisher.api_urls
"""

from django.urls import path

from . import views

app_name = 'wagtailsnapshotpublisher_api'
urlpatterns = [
    path('<slug:site_code>/<slug:type>/<slug:key>/', views.get_document_release,
         name='get-document-release-page'),
    path('<slug:site_code>/<uuid:content_release_uuid>/<slug:type>/<slug:key>/',
         views.get_document_release, name='get-document-release-page'),
]
