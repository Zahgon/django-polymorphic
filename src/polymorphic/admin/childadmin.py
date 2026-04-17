"""
The child admin displays the change/delete view of the subclass model.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Generic

from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from typing_extensions import TypeVar

from polymorphic.models import PolymorphicModel
from polymorphic.utils import get_base_polymorphic_model

from ..admin import PolymorphicParentModelAdmin

_ModelT = TypeVar("_ModelT", bound=PolymorphicModel, default=PolymorphicModel)

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[_ModelT]
else:
    _ModelAdminBase = admin.ModelAdmin


class ParentAdminNotRegistered(RuntimeError):
    "The admin site for the model is not registered."


class PolymorphicChildModelAdmin(_ModelAdminBase, Generic[_ModelT]):
    """
    The *optional* base class for the admin interface of derived models.

    This base class defines some convenience behavior for the admin interface:

    * It corrects the breadcrumbs in the admin pages.
    * It adds the base model to the template lookup paths.
    * It allows to set ``base_form`` so the derived class will automatically include other fields in the form.
    * It allows to set ``base_fieldsets`` so the derived class will automatically display any extra fields.
    """

    #: The base model that the class uses (auto-detected if not set explicitly)
    base_model: type[models.Model] | None = None

    #: By setting ``base_form`` instead of ``form``, any subclass fields are automatically added to the form.
    #: This is useful when your model admin class is inherited by others.
    base_form: type[ModelForm[Any]] | None = None

    #: By setting ``base_fieldsets`` instead of ``fieldsets``,
    #: any subclass fields can be automatically added.
    #: This is useful when your model admin class is inherited by others.
    base_fieldsets: Any = None

    #: Default title for extra fieldset
    extra_fieldset_title = _("Contents")

    #: Whether the child admin model should be visible in the admin index page.
    show_in_index = False

    def __init__(self, model: type[_ModelT], admin_site: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(model, admin_site, *args, **kwargs)

        if self.base_model is None:
            self.base_model = get_base_polymorphic_model(model)

    def get_form(
        self, request: HttpRequest, obj: Any | None = None, change: bool = False, **kwargs: Any
    ) -> type[ModelForm[Any]]:
        # The django admin validation requires the form to have a 'class Meta: model = ..'
        # attribute, or it will complain that the fields are missing.
        # However, this enforces all derived ModelAdmin classes to redefine the model as well,
        # because they need to explicitly set the model again - it will stick with the base model.
        #
        # Instead, pass the form unchecked here, because the standard ModelForm will just work.
        # If the derived class sets the model explicitly, respect that setting.
        kwargs.setdefault("form", self.base_form or self.form)

        # prevent infinite recursion when this is called from get_subclass_fields
        if not self.fieldsets and not self.fields:
            kwargs.setdefault("fields", "__all__")

        return super().get_form(request, obj, **kwargs)











    # ---- Extra: improving the form/fieldset default display ----



