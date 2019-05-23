"""
.. module:: wagtailsnapshotpublisher.panels
"""

from django.forms.utils import pretty_name
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import EditHandler, FieldPanel


class BaseReadOnlyPanel(EditHandler):
    """ BaseReadOnlyPanel """

    def render(self):
        """ render """
        value = getattr(self.instance, self.attr)
        if callable(value):
            value = value()
        return format_html('<div style="padding-top: 1.2em;">{}</div>', value)

    def render_as_object(self):
        """ render_as_object """
        return format_html(
            '<fieldset><legend>{}</legend>'
            '<ul class="fields"><li><div class="field">{}</div></li></ul>'
            '</fieldset>',
            self.heading, self.render())

    def render_as_field(self):
        """ render_as_field """
        return format_html(
            '<div class="field">'
            '<label>{}{}</label>'
            '<div class="field-content">{}</div>'
            '</div>',
            self.heading, _(':'), self.render())

    def required_fields(self):
        """ required_fields """
        fields = []
        return fields


class ReadOnlyPanel:
    """ ReadOnlyPanel """

    def __init__(self, attr, heading=None, classname='', help_text=''):
        """ __init__ """
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname
        self.help_text = help_text

        def required_fields(self):
            """ required_fields """
            raise AttributeError

    def bind_to(self, model):
        """ bind_to """
        return type(str(_('ReadOnlyPanel')), (BaseReadOnlyPanel,),
                    {'attr': self.attr, 'heading': self.heading,
                     'classname': self.classname})(heading=self.heading,
                                                   classname=self.classname,
                                                   help_text=self.help_text)


class BaseEditableOnCreatedPanel(FieldPanel):
    """ BaseEditableOnCreatedPanel """

    def render_as_object(self):
        """ render_as_object """
        if self.instance.id is not  None:
            value = getattr(self.instance, self.attr)
            if callable(value):
                value = value()
            return format_html(
                '<fieldset><legend>{}</legend>'
                '<ul class="fields"><li><div class="field"><div style="padding-top: 1.2em;">{}</div></div></li></ul>'
                '</fieldset>',
                self.heading, value)
        return super(BaseEditableOnCreatedPanel, self).render_as_object()


class EditableOnCreatedPanel:
    """ EditableOnCreatedPanel """
    def __init__(self, attr, heading=None, classname='', help_text=''):
        """ __init__ """
        self.attr = attr
        self.heading = pretty_name(self.attr) if heading is None else heading
        self.classname = classname
        self.help_text = help_text

        def required_fields(self):
            """ required_fields """
            raise AttributeError

    def bind_to(self, model):
        """ bind_to """
        return type(str(_('EditableOnCreatedPanel')), (BaseEditableOnCreatedPanel,),
                    {'attr': self.attr, 'heading': self.heading,
                     'classname': self.classname})(field_name=self.attr,
                                                   heading=self.heading,
                                                   classname=self.classname,
                                                   help_text=self.help_text)
