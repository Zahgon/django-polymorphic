from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .parentadmin import PolymorphicParentModelAdmin


class PolymorphicChildModelFilter(admin.SimpleListFilter):
    """
    An admin list filter for the PolymorphicParentModelAdmin which enables
    filtering by its child models.

    This can be used in the parent admin:

    .. code-block:: python

        list_filter = (PolymorphicChildModelFilter,)
    """

    title: str = _("Type")  # type: ignore[assignment]
    parameter_name: str = "polymorphic_ctype"


