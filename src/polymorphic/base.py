"""
PolymorphicModel Meta Class
"""

import sys
import warnings
from typing import Any, cast

from django.db import models
from django.db.models.base import ModelBase
from django.db.models.options import Options

from .deletion import PolymorphicGuard
from .managers import PolymorphicManager
from .related_descriptors import (
    NonPolymorphicForwardOneToOneDescriptor,
    NonPolymorphicReverseOneToOneDescriptor,
)
from .utils import _clear_utility_caches

# PolymorphicQuerySet Q objects (and filter()) support these additional key words.
# These are forbidden as field names (a descriptive exception is raised)
POLYMORPHIC_SPECIAL_Q_KWORDS: set[str] = {"instance_of", "not_instance_of"}


class ManagerInheritanceWarning(RuntimeWarning):
    pass


# check that we're on cpython to enable dumpdata frame inspection guard
check_dump: bool = hasattr(sys, "_getframe")


# We wrap the base_manager property to return a PolymorphicManager
# for polymorphic models when the base manager would otherwise
# be the default auto-created manager. This ensures that
# reverse relations to polymorphic models also use polymorphic
# querysets by default.
# https://github.com/jazzband/django-polymorphic/pull/858
dj_base_manager = Options.base_manager.func  # type: ignore[attr-defined]


def polymorphic_base_manager(self):
    """
    Return a polymorphic base manager for polymorphic models.
    """
    pass


setattr(Options.base_manager, "func", polymorphic_base_manager)


class PolymorphicModelBase(ModelBase):
    """
    Manager inheritance is a pretty complex topic which may need
    more thought regarding how this should be handled for polymorphic
    models.

    In any case, we probably should propagate 'objects' and 'base_objects'
    from PolymorphicModel to every subclass. We also want to somehow
    inherit/propagate _default_manager as well, as it needs to be polymorphic.

    The current implementation below is an experiment to solve this
    problem with a very simplistic approach: We unconditionally
    inherit/propagate any and all managers (using _copy_to_model),
    as long as they are defined on polymorphic models
    (the others are left alone).

    Like Django ModelBase, we special-case _default_manager:
    if there are any user-defined managers, it is set to the first of these.

    We also require that _default_manager as well as any user defined
    polymorphic managers produce querysets that are derived from
    PolymorphicQuerySet.

    We also replace the parent/child relation field descriptors with versions that will
    use non-polymorphic querysets.

    If we have inheritance of the form ModelA -> ModelB ->ModelC then
    Django creates accessors like this:
    - ModelA: modelb
    - ModelB: modela_ptr, modelb, modelc
    - ModelC: modela_ptr, modelb, modelb_ptr, modelc

    These accessors allow Django (and everyone else) to travel up and down
    the inheritance tree for the db object at hand. This is important for deletion among
    other things.
    """

    def __new__(
        cls, model_name: str, bases: tuple[type, ...], attrs: dict[str, Any], **kwargs: Any
    ) -> type:
        # skip special setup for PolymorphicModel itself
        if attrs.pop("_meta_skip", False):
            return super().__new__(cls, model_name, bases, attrs, **kwargs)

        from .models import PolymorphicModel

        new_class = cast(
            type[PolymorphicModel], super().__new__(cls, model_name, bases, attrs, **kwargs)
        )

        # wrap on_delete handlers of reverse relations back to this model with the
        # polymorphic deletion guard
        for fk in new_class._meta.fields:
            if isinstance(fk, (models.ForeignKey, models.OneToOneField)) and not isinstance(
                fk.remote_field.on_delete, PolymorphicGuard
            ):
                fk.remote_field.on_delete = PolymorphicGuard(fk.remote_field.on_delete)

        # replace the parent/child descriptors
        if new_class._meta.parents and not (new_class._meta.abstract or new_class._meta.proxy):


            replace_inheritance_descriptors(new_class)
        _clear_utility_caches()
        return new_class




