"""
.. module:: wagtailsnapshotpublisher.custom_admin_urls
"""

from django.urls import path

from . import views


# Override Wagtail paths
app_name = 'wagtailsnapshotpublisher_admin'
urlpatterns = [
    path('pages/<int:page_id>/unpublish/<int:release_id>/', views.unpublish_page,
         name='unpublish_page_from_release'),
    path('pages/<int:page_id>/unpublish/<int:release_id>/recursively/',
         views.unpublish_recursively_page, name='unpublish_recursively_page_from_release'),
    path('pages/<int:page_id>/remove/<int:release_id>/', views.remove_page,
         name='remove_page_from_release'),
    path('pages/<int:page_id>/remove/<int:release_id>/recursively/', views.remove_recursively_page,
         name='remove_recursively_page_from_release'),

    path('<slug:content_app>/<slug:content_class>/unpublish/<int:content_id>/<int:release_id>/',
         views.unpublish, name='unpublish_from_release'),
    path('<slug:content_app>/<slug:content_class>/edit/<int:content_id>/preview/<slug:preview_mode>/',
         views.preview_model, name='preview_model_admin'),
    path('<slug:content_app>/<slug:content_class>/<int:content_id>/preview/<slug:preview_mode>/',
         views.preview_instance, name='preview_instance_admin'),

    path('wagtailsnapshotpublisher/wsspcontentrelease/details/<int:release_id>/',
         views.release_detail, name='release_detail'),
    path('wagtailsnapshotpublisher/wsspcontentrelease/setstage/<int:release_id>/',
         views.release_set_stage, name='release_set_stage'),
    path('wagtailsnapshotpublisher/wsspcontentrelease/setstagedetails/<int:release_id>/',
         views.release_detail,
         {'set_stage_button': True},
         name='release_set_stage_detail',
     ),
     path('wagtailsnapshotpublisher/wsspcontentrelease/unsetstagedetails/<int:release_id>/',
         views.release_unset_stage,
         name='release_unset_stage_detail',
     ),
    path('wagtailsnapshotpublisher/wsspcontentrelease/setlive/<int:release_id>/',
         views.release_set_live, name='release_set_live'),
    path('wagtailsnapshotpublisher/wsspcontentrelease/setlivedetails/<int:release_id>/',
         views.release_detail,
         {'set_live_button': True},
         name='release_set_live_detail',
     ),
    path('wagtailsnapshotpublisher/wsspcontentrelease/archive/<int:release_id>/',
         views.release_archive, name='release_archive'),
    path('wagtailsnapshotpublisher/wsspcontentrelease/restore/<int:release_id>/',
         views.release_restore, name='release_restore'),
    path('wagtailsnapshotpublisher/wsspcontentrelease/unfreeze/<int:release_id>/',
         views.release_unfreeze, name='release_unfreeze'),
]
