from django.templatetags.static import static
from django.urls import resolve
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.forms.models import AbstractForm
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.core import hooks

from .models import WSSPContentRelease


class ReleaseAdmin(ModelAdmin):
    model = WSSPContentRelease
    menu_label = 'Releases'
    menu_icon = 'date'
    menu_order = 900 

    list_display = ('site_code', 'title', 'uuid', 'status', 'publish_datetime')
    list_filter = ('status', 'site_code',)
    search_fields = ('title',)
    ordering = ('status', '-publish_datetime')
    index_view_extra_css = 'wagtailadmin/css/list-release.css',

    def get_extra_attrs_for_row(self, obj, context):
        classname = ''
        if obj == obj.__class__.objects.live(site_code=obj.site_code):
            classname = 'is-live'
        elif obj.__class__.objects.lives(site_code=obj.site_code).filter(id=obj.id).exists():
            classname = 'was-live'

        return {
            'class': classname,
        }

modeladmin_register(ReleaseAdmin)


class ReleaseActionMenuItem (ActionMenuItem):
    def is_shown(self, request, context):
        if context['view'] == 'edit' and 'page' in context and \
                hasattr(context['page'], 'content_release'):
            return (
                not context['page'].locked
                and context['user_page_permissions'].for_page(context['page']).can_publish()
            )
        return False


class PublishToReleaseMenuItem(ReleaseActionMenuItem):
    label = _('Publish To A Release')
    name = 'wssp-action-publish-release'


class UnpublishToReleaseMenuItem(ReleaseActionMenuItem):
    label = _('Unpublish From A Release')
    name = 'wssp-action-unpublish-release'


@hooks.register('register_page_action_menu_item')
def register_publish_to_release_menu_item():
    return PublishToReleaseMenuItem(order=10)

@hooks.register('register_page_action_menu_item')
def register_unpublish_to_release_menu_item():
    return UnpublishToReleaseMenuItem(order=20)

@hooks.register('construct_page_action_menu')
def remove_submit_to_moderator_option(menu_items, request, context):
    if context['view'] == 'create' or (context['view'] == 'edit' and 'page' in context and hasattr(context['page'], 'content_release')):
        menu_items[:] = [item for item in menu_items if item.name and item.name.startswith('wssp-action-')]

@hooks.register('insert_editor_js')
def add_release_js():
    js_files = [
        'wagtailadmin/js/edit-action-release.js',
    ]
    js_includes = format_html_join('\n', '<script src="{0}"></script>',
        ((static(filename),) for filename in js_files)
    )
    return js_includes


@hooks.register('insert_editor_css')
def add_release_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static('wagtailadmin/css/edit-action-release.css')
    )
