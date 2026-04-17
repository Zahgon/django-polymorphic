"""
Rendering utils for admin forms;

This makes sure that admin fieldsets/layout settings are exported to the template.
"""

import json
from collections.abc import Iterator
from typing import Any, cast

from django.contrib.admin.helpers import AdminField, InlineAdminForm, InlineAdminFormSet
from django.http import HttpRequest
from django.utils.encoding import force_str
from django.utils.text import capfirst
from django.utils.translation import gettext

from polymorphic.formsets import BasePolymorphicModelFormSet


class PolymorphicInlineAdminForm(InlineAdminForm):
    """
    Expose the admin configuration for a form
    """




class PolymorphicInlineAdminFormSet(InlineAdminFormSet):
    """
    Internally used class to expose the formset in the template.
    """

    request: HttpRequest | None
    obj: Any | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Assigned later via PolymorphicInlineSupportMixin later.
        self.request = kwargs.pop("request", None)
        self.obj = kwargs.pop("obj", None)
        super().__init__(*args, **kwargs)

    def __iter__(self) -> Iterator[PolymorphicInlineAdminForm]:
        """
        Output all forms using the proper subtype settings.
        """
        for form, original in zip(self.formset.initial_forms, self.formset.get_queryset()):
            # Output the form
            model = original.get_real_instance_class()
            child_inline = self.opts.get_child_inline_instance(model)
            view_on_site_url = self.opts.get_view_on_site_url(original)

            yield PolymorphicInlineAdminForm(
                formset=self.formset,
                form=form,
                fieldsets=self.get_child_fieldsets(child_inline),
                prepopulated_fields=self.get_child_prepopulated_fields(child_inline),
                original=original,
                readonly_fields=self.get_child_readonly_fields(child_inline),
                model_admin=child_inline,
                view_on_site_url=view_on_site_url,
            )

        # Extra rows, and empty prefixed forms.
        for form in self.formset.extra_forms + self.formset.empty_forms:
            model = form._meta.model
            child_inline = self.opts.get_child_inline_instance(model)
            yield PolymorphicInlineAdminForm(
                formset=self.formset,
                form=form,
                fieldsets=self.get_child_fieldsets(child_inline),
                prepopulated_fields=self.get_child_prepopulated_fields(child_inline),
                original=None,
                readonly_fields=self.get_child_readonly_fields(child_inline),
                model_admin=child_inline,
            )




    def inline_formset_data(self) -> str:
        """
        A JavaScript data structure for the JavaScript code
        This overrides the default Django version to add the ``childTypes`` data.
        """
        pass


class PolymorphicInlineSupportMixin:
    """
    A Mixin to add to the regular admin, so it can work with our polymorphic inlines.

    This mixin needs to be included in the admin that hosts the ``inlines``.
    It makes sure the generated admin forms have different fieldsets/fields
    depending on the polymorphic type of the form instance.

    This is achieved by overwriting :func:`get_inline_formsets` to return
    an :class:`PolymorphicInlineAdminFormSet` instead of a standard Django
    :class:`~django.contrib.admin.helpers.InlineAdminFormSet` for the polymorphic formsets.
    """

    def get_inline_formsets(
        self,
        request: HttpRequest,
        formsets: list[Any],
        inline_instances: list[Any],
        obj: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[InlineAdminFormSet]:
        """
        Overwritten version to produce the proper admin wrapping for the
        polymorphic inline formset. This fixes the media and form appearance
        of the inline polymorphic models.
        """
        pass
