from django.contrib.auth.models import Permission
from django.templatetags.static import static
from django.urls import resolve, reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.action_menu import ActionMenuItem
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.contrib.forms.models import AbstractForm
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.core import hooks

from .models import WSSPContentRelease


class ReleaseButtonHelper(ButtonHelper):

    def get_buttons_for_obj(self, obj, exclude=None, classnames_add=None,
                            classnames_exclude=None):
        btns = ButtonHelper.get_buttons_for_obj(self, obj, exclude=None, classnames_add=None, classnames_exclude=None)
        
        if obj == obj.__class__.objects.live(site_code=obj.site_code):
            pass
        elif not obj.__class__.objects.lives(site_code=obj.site_code).filter(id=obj.id).exists():
            btns.insert(1, self.detail_revision_button(obj, ['button'], classnames_exclude))
            if obj.status >= 1 and obj.publish_datetime != None:
                btns.insert(2, self.unfreeze_button(obj, ['button'], classnames_exclude))
            else:
                btns.insert(2, self.set_live_revision_button(obj, ['button'], classnames_exclude))
        elif obj.__class__.objects.lives(site_code=obj.site_code).filter(id=obj.id).exists():
            btns.insert(1, self.archive_revision_button(obj, ['button'], classnames_exclude))
            btns.insert(2, self.restore_button(obj, ['button'], classnames_exclude))
        return btns

    def create_button(self, label, title, url, classnames_add=None, classnames_exclude=None):
        if classnames_add is None:
            classnames_add = []
        if classnames_exclude is None:
            classnames_exclude = []
        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)

        return {
            'url': url,
            'label': _(label),
            'classname': cn,
            'title': _(title),
        }

    def detail_revision_button(self, obj, classnames_add=None, classnames_exclude=None):
        url = reverse('wagtailsnapshotpublisher_custom_admin:release-detail', kwargs={'release_id': obj.pk})
        return self.create_button('detail', 'Detail updated pages for this release', url, classnames_add, classnames_exclude)
    
    def set_live_revision_button(self, obj, classnames_add=None, classnames_exclude=None):
        url = reverse('wagtailsnapshotpublisher_custom_admin:release-set-live-detail', kwargs={'release_id': obj.pk})
        return self.create_button('set live', 'Set this release live', url, classnames_add, classnames_exclude)
    
    def archive_revision_button(self, obj, classnames_add=None, classnames_exclude=None):
        url = reverse('wagtailsnapshotpublisher_custom_admin:release-archive', kwargs={'release_id': obj.pk})
        return self.create_button('archive', 'Archive this release', url, classnames_add, classnames_exclude)

    def restore_button(self, obj, classnames_add=None, classnames_exclude=None):
        url = reverse('wagtailsnapshotpublisher_custom_admin:release-restore', kwargs={'release_id': obj.pk})
        return self.create_button('restore', 'Restore', url, classnames_add, classnames_exclude)

    def unfreeze_button(self, obj, classnames_add=None, classnames_exclude=None):
        url = reverse('wagtailsnapshotpublisher_custom_admin:release-unfreeze', kwargs={'release_id': obj.pk})
        return self.create_button('unfreeze', 'Unfreeze', url, classnames_add, classnames_exclude)


class ReleaseAdmin(ModelAdmin):
    model = WSSPContentRelease
    menu_label = 'Releases'
    menu_icon = 'date'
    menu_order = 900 

    list_display = ('site_code', 'title', 'uuid', 'status', 'publish_datetime', 'version')
    list_filter = ('status', 'site_code',)
    search_fields = ('title',)
    ordering = ('status', '-publish_datetime')
    index_view_extra_css = ('wagtailadmin/css/list-release.css',)

    def get_extra_attrs_for_row(self, obj, context):
        classname = ''
        if obj == obj.__class__.objects.live(site_code=obj.site_code):
            classname = 'is-live'
        elif obj.__class__.objects.lives(site_code=obj.site_code).filter(id=obj.id).exists():
            classname = 'was-live'
        elif obj.status == 1 and obj.publish_datetime is not None:
            classname = 'is-frozen'

        return {
            'class': classname,
        }
    
    def get_button_helper_class(self):
        """
        Returns a ButtonHelper class to help generate buttons for the given
        model.
        """
        return ReleaseButtonHelper

    def get_queryset(self, request):
        return super(ReleaseAdmin, self).get_queryset(request).exclude(status=2)
    
    def get_edit_handler(self, instance, request):
        from wagtail.admin.edit_handlers import ObjectList
        panels = self.model.panels
        if instance.status >= 1 and instance.publish_datetime:
            panels = self.model.panels_live_release
        return ObjectList(panels)

    edit_template_name = 'modeladmin/edit_release.html'

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
    name = 'wssp-actionrelease-publish-release'


class UnpublishToReleaseMenuItem(ReleaseActionMenuItem):
    label = _('Unpublish From A Release')
    name = 'wssp-actionrelease-unpublish-release'


class RemoveFromReleaseMenuItem(ReleaseActionMenuItem):
    label = _('Remove From A Release')
    name = 'wssp-actionrelease-remove-release'


class PublishToLiveReleaseMenuItem(ReleaseActionMenuItem):
    label = _('Publish Directly To Live')
    name = 'wssp-actionliverelease-publish-live-release'


@hooks.register('register_page_action_menu_item')
def register_publish_to_release_menu_item():
    return PublishToReleaseMenuItem(order=30)

@hooks.register('register_page_action_menu_item')
def register_unpublish_to_release_menu_item():
    return UnpublishToReleaseMenuItem(order=20)

@hooks.register('register_page_action_menu_item')
def register_remove_from_release_menu_item():
    return RemoveFromReleaseMenuItem(order=10)

@hooks.register('register_page_action_menu_item')
def register_publish_to_live_release_menu_item():
    return PublishToLiveReleaseMenuItem(order=40)

@hooks.register('construct_page_action_menu')
def remove_submit_to_moderator_option(menu_items, request, context):
    if context['view'] == 'create':
        menu_items[:] = [item for item in menu_items if item.name and item.name.startswith('wssp-action')]

    if context['view'] == 'edit' and 'page' in context and hasattr(context['page'], 'content_release'):
        if hasattr(context['page'].__class__, 'release_config'):
            items = []
            if 'can_publish_to_release' in context['page'].__class__.release_config and context['page'].__class__.release_config['can_publish_to_release']:
                items += [item for item in menu_items if item.name and item.name.startswith('wssp-actionrelease-')]
            if 'can_publish_to_live_release' in context['page'].__class__.release_config and context['page'].__class__.release_config['can_publish_to_live_release']:
                items += [item for item in menu_items if item.name and item.name.startswith('wssp-actionliverelease-')]
            menu_items[:] = items


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

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static('wagtailadmin/css/custom_release.css')
    )

@hooks.register('register_permissions')
def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_dev')


class ModelAdminWithRelease(ModelAdmin):
    edit_template_name = 'modeladmin/edit_with_release.html'
