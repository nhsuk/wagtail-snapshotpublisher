from django.urls import path

from . import views


# Override Wagtail paths
app_name = 'wagtailsnapshotpublisher_custom_admin'
urlpatterns = [
    path('pages/<int:page_id>/unpublish/<int:release_id>/', views.unpublish_page, name='unpublish-page-from-release'),
    path('<slug:content_app>/<slug:content_class>/unpublish/<int:content_id>/<int:release_id>/', views.unpublish, name='unpublish-from-release'),
]