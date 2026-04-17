"""
Django Admin support for polymorphic inlines.

Each row in the inline can correspond with a different subclass.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, cast

from django.conf import settings
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.utils import flatten_fieldsets
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms import Media
from django.http import HttpRequest

from polymorphic.formsets import (
    BasePolymorphicInlineFormSet,
    PolymorphicFormSetChild,
    UnsupportedChildType,
    polymorphic_child_forms_factory,
)
from polymorphic.formsets.utils import add_media

from .helpers import PolymorphicInlineSupportMixin

if TYPE_CHECKING:
    from django.contrib.admin.options import _FieldGroups, _FieldsetSpec


class PolymorphicInlineModelAdmin(InlineModelAdmin):
    """
    A polymorphic inline, where each formset row can be a different form.

    Note that:

    * Permissions are only checked on the base model.
    * The child inlines can't override the base model fields, only this parent inline can do that.
    """

    formset: type[BasePolymorphicInlineFormSet] = BasePolymorphicInlineFormSet

    #: The extra media to add for the polymorphic inlines effect.
    #: This can be redefined for subclasses.
    polymorphic_media: Media = Media(
        js=(
            f"admin/js/vendor/jquery/{'jquery' if settings.DEBUG else 'jquery.min'}.js",
            "admin/js/jquery.init.js",
            "polymorphic/js/polymorphic_inlines.js",
        ),
        css={"all": ("polymorphic/css/polymorphic_inlines.css",)},
    )

    #: The extra forms to show
    #: By default there are no 'extra' forms as the desired type is unknown.
    #: Instead, add each new item using JavaScript that first offers a type-selection.
    extra: int = 0

    #: Inlines for all model sub types that can be displayed in this inline.
    #: Each row is a :class:`PolymorphicInlineModelAdmin.Child`
    child_inlines: list[type["PolymorphicInlineModelAdmin.Child"]] = []

    child_inline_instances: list["PolymorphicInlineModelAdmin.Child"]

    def __init__(self, parent_model: type[models.Model], admin_site: AdminSite) -> None:
        super().__init__(parent_model, admin_site)

        # Extra check to avoid confusion
        # While we could monkeypatch the admin here, better stay explicit.
        parent_admin = admin_site._registry.get(parent_model, None)
        if parent_admin is not None:  # Can be None during check
            if not isinstance(parent_admin, PolymorphicInlineSupportMixin):
                raise ImproperlyConfigured(
                    "To use polymorphic inlines, add the `PolymorphicInlineSupportMixin` mixin "
                    "to the ModelAdmin that hosts the inline."
                )

        # While the inline is created per request, the 'request' object is not known here.
        # Hence, creating all child inlines unconditionally, without checking permissions.
        self.child_inline_instances = self.get_child_inline_instances()

        # Create a lookup table
        self._child_inlines_lookup = {}
        for child_inline in self.child_inline_instances:
            self._child_inlines_lookup[child_inline.model] = child_inline

    def get_child_inlines(self) -> list[type["PolymorphicInlineModelAdmin.Child"]]:
        """
        Return the derived inline classes which this admin should handle.

        This should return an iterable of
        :class:`~polymorphic.admin.inlines.PolymorphicInlineModelAdmin.Child` classes,
        to override :attr:`~polymorphic.admin.inlines.PolymorphicInlineModelAdmin.child_inlines`.
        """
        pass

    def get_child_inline_instances(self) -> list["PolymorphicInlineModelAdmin.Child"]:
        """
        :rtype List[PolymorphicInlineModelAdmin.Child]
        """
        pass

    def get_child_inline_instance(
        self, model: type[models.Model]
    ) -> "PolymorphicInlineModelAdmin.Child":
        """
        Find the child inline for a given model.

        :rtype: PolymorphicInlineModelAdmin.Child
        """
        pass

    def get_formset(
        self, request: HttpRequest, obj: Any = None, **kwargs: Any
    ) -> type[BasePolymorphicInlineFormSet]:
        """
        Construct the inline formset class.

        This passes all class attributes to the formset.

        :rtype: type
        """
        pass

    def get_formset_children(
        self, request: HttpRequest, obj: Any = None
    ) -> list[PolymorphicFormSetChild]:
        """
        The formset 'children' provide the details for all child models that are part of this formset.
        It provides a stripped version of the modelform/formset factory methods.
        """
        pass

    def get_fieldsets(self, request: HttpRequest, obj: Any = None) -> "_FieldsetSpec":
        """
        Hook for specifying fieldsets.
        """
        pass



    class Child(InlineModelAdmin):
        """
        The child inline; which allows configuring the admin options
        for the child appearance.

        Note that not all options will be honored by the parent, notably the formset options:
        * :attr:`extra`
        * :attr:`min_num`
        * :attr:`max_num`

        The model form options however, will all be read.
        """

        formset_child: type[PolymorphicFormSetChild] = PolymorphicFormSetChild
        extra: int = 0  # TODO: currently unused for the children.
        parent_inline: "PolymorphicInlineModelAdmin"

        def __init__(self, parent_inline: "PolymorphicInlineModelAdmin") -> None:
            self.parent_inline = parent_inline
            super(PolymorphicInlineModelAdmin.Child, self).__init__(
                parent_inline.parent_model, parent_inline.admin_site
            )

        def get_formset(self, request: HttpRequest, obj: Any = None, **kwargs: Any) -> None:  # type: ignore[override]
            # The child inline is only used to construct the form,
            # and allow to override the form field attributes.
            # The formset is created by the parent inline.
            raise RuntimeError("The child get_formset() is not used.")


        def get_formset_child(
            self, request: HttpRequest, obj: Any = None, **kwargs: Any
        ) -> PolymorphicFormSetChild:
            """
            Return the formset child that the parent inline can use to represent us.

            :rtype: PolymorphicFormSetChild
            """
            pass


class StackedPolymorphicInline(PolymorphicInlineModelAdmin):
    """
    Stacked inline for django-polymorphic models.
    Since tabular doesn't make much sense with changed fields, just offer this one.
    """

    #: The default template to use.
    template: str = "admin/polymorphic/edit_inline/stacked.html"
