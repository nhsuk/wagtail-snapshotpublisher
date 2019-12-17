"""
.. module:: wagtailsnapshotpublisher.api_urls
"""

from django.urls import path

from . import views

app_name = 'wagtailsnapshotpublisher_api'
urlpatterns = [
    path('<slug:site_code>/<slug:content_type>/<slug:content_key>/', views.get_document_release,
         name='live_document_release_page'),
    path('<slug:site_code>/<uuid:content_release_uuid>/<slug:content_type>/<slug:content_key>/',
         views.get_document_release, name='document_release_page'),
    path('<slug:site_code>/releases/',
         views.get_releases, name='site_releases'),
]
