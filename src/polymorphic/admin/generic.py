from __future__ import annotations

from typing import Any, cast

from django.contrib.contenttypes.admin import GenericInlineModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.utils.functional import cached_property

from polymorphic.formsets import (
    BaseGenericPolymorphicInlineFormSet,
    GenericPolymorphicFormSetChild,
    PolymorphicFormSetChild,
    polymorphic_child_forms_factory,
)

from .inlines import PolymorphicInlineModelAdmin


class GenericPolymorphicInlineModelAdmin(PolymorphicInlineModelAdmin, GenericInlineModelAdmin):
    """
    Base class for variation of inlines based on generic foreign keys.
    """

    #: The formset class
    formset: type[BaseGenericPolymorphicInlineFormSet] = BaseGenericPolymorphicInlineFormSet  # type: ignore[assignment]

    def get_formset(  # type: ignore[override]
        self, request: HttpRequest, obj: Any = None, **kwargs: Any
    ) -> type[BaseGenericPolymorphicInlineFormSet]:
        """
        Construct the generic inline formset class.
        """
        pass

    class Child(PolymorphicInlineModelAdmin.Child):
        """
        Variation for generic inlines.
        """

        # Make sure that the GFK fields are excluded from the child forms
        formset_child: type[GenericPolymorphicFormSetChild] = GenericPolymorphicFormSetChild
        ct_field: str = "content_type"
        ct_fk_field: str = "object_id"

        @cached_property
        def content_type(self) -> ContentType:
            """
            Expose the ContentType that the child relates to.
            This can be used for the ``polymorphic_ctype`` field.
            """
            pass



class GenericStackedPolymorphicInline(GenericPolymorphicInlineModelAdmin):
    """
    The stacked layout for generic inlines.
    """

    #: The default template to use.
    template: str = "admin/polymorphic/edit_inline/stacked.html"
