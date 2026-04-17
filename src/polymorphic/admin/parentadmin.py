"""
The parent admin displays the list view of the base model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, cast

from django.contrib import admin
from django.contrib.admin.helpers import AdminErrorList, AdminForm
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import models
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from typing_extensions import TypeVar

from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet
from polymorphic.utils import get_base_polymorphic_model

from .forms import PolymorphicModelChoiceForm

_ModelT = TypeVar("_ModelT", bound=PolymorphicModel, default=PolymorphicModel)

if TYPE_CHECKING:
    _ModelAdminBase = admin.ModelAdmin[_ModelT]
else:
    _ModelAdminBase = admin.ModelAdmin


class RegistrationClosed(RuntimeError):
    "The admin model can't be registered anymore at this point."


class ChildAdminNotRegistered(RuntimeError):
    "The admin site for the model is not registered."


class PolymorphicParentModelAdmin(_ModelAdminBase, Generic[_ModelT]):
    """
    A admin interface that can displays different change/delete pages, depending on the polymorphic model.
    To use this class, one attribute need to be defined:

    * :attr:`child_models` should be a list models.

    Alternatively, the following methods can be implemented:

    * :func:`get_child_models` should return a list of models.
    * optionally, :func:`get_child_type_choices` can be overwritten to refine the choices for the add dialog.

    This class needs to be inherited by the model admin base class that is registered in the site.
    The derived models should *not* register the ModelAdmin, but instead it should be returned by :func:`get_child_models`.
    """

    #: The base model that the class uses (auto-detected if not set explicitly)
    base_model: type[models.Model] | None = None

    #: The child models that should be displayed
    child_models: list[type[models.Model]] | None = None

    #: Whether the list should be polymorphic too, leave to ``False`` to optimize
    polymorphic_list = False

    add_type_template = None
    add_type_form = PolymorphicModelChoiceForm

    #: The regular expression to filter the primary key in the URL.
    #: This accepts only numbers as defensive measure against catch-all URLs.
    #: If your primary key consists of string values, update this regular expression.
    pk_regex = r"(\d+|__fk__)"

    def __init__(self, model: type[_ModelT], admin_site: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(model, admin_site, *args, **kwargs)
        self._is_setup = False

        if self.base_model is None:
            self.base_model = get_base_polymorphic_model(model)


    def get_child_models(self):
        """
        Return the derived model classes which this admin should handle.
        This should return a list of tuples, exactly like :attr:`child_models` is.

        The model classes can be retrieved as ``base_model.__subclasses__()``,
        a setting in a config file, or a query of a plugin registration system at your option
        """
        pass

    def get_child_type_choices(self, request, action):
        """
        Return a list of polymorphic types for which the user has the permission to perform the given action.
        """
        pass





    def add_view(self, request, form_url="", extra_context=None):
        """Redirect the add view to the real admin."""
        pass

    def change_view(self, request, object_id, *args, **kwargs):
        """Redirect the change view to the real admin."""
        pass


    def history_view(self, request, object_id, extra_context=None):
        """Redirect the history view to the real admin."""
        pass

    def delete_view(self, request, object_id, extra_context=None):
        """Redirect the delete view to the real admin."""
        pass

    def get_urls(self):
        """
        Expose the custom URLs for the subclasses and the URL resolver.
        """
        pass

    def add_type_view(self, request, form_url=""):
        """
        Display a choice form to select which page type to add.
        """
        pass

    def render_add_type_form(self, request, context, form_url=""):
        """
        Render the page type choice form.
        """
        pass

