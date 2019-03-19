# from django.templatetags.static import static
# from django.urls import resolve
# from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

# from wagtail.admin.action_menu import ActionMenuItem
from wagtail.contrib.modeladmin.menus import GroupMenuItem, ModelAdminMenuItem, SubMenu
# from wagtail.admin.edit_handlers import FieldPanel
# from wagtail.contrib.forms.models import AbstractForm
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.core import hooks

from .models import TestSnippet


class TestSnippetAdmin(ModelAdmin):
    model = TestSnippet
    menu_label = 'TestSnippet'
    menu_order = 950

    list_display = ('name',)
    search_fields = ('name',)
    edit_template_name = 'modeladmin/edit.html'

modeladmin_register(TestSnippetAdmin)