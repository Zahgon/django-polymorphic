"""
Seamless Polymorphic Inheritance for Django Models
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from typing import ClassVar, cast

from django.contrib.contenttypes.models import ContentType
from django.db import models, router, transaction
from django.db.models import Q
from django.db.models.base import ModelBase
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils.functional import classproperty
from typing_extensions import Self

from .base import PolymorphicModelBase
from .managers import PolymorphicManager
from .query_translate import translate_polymorphic_Q_object
from .utils import get_base_polymorphic_model, lazy_ctype

###################################################################################
# PolymorphicModel


class PolymorphicTypeUndefined(LookupError): ...


class PolymorphicTypeInvalid(RuntimeError): ...


class PolymorphicModel(models.Model, metaclass=PolymorphicModelBase):
    """
    Abstract base class that provides polymorphic behaviour
    for any model directly or indirectly derived from it.

    PolymorphicModel declares one field for internal use (:attr:`polymorphic_ctype`)
    and provides a polymorphic manager as the default manager (and as 'objects').
    """

    _meta_skip: ClassVar[bool] = True

    # for PolymorphicModelBase, so it can tell which models are polymorphic and which are not (duck typing)
    polymorphic_model_marker: ClassVar[bool] = True

    # for PolymorphicQuery, True => an overloaded __repr__ with nicer multi-line output is used by PolymorphicQuery
    polymorphic_query_multiline_output: ClassVar[bool] = False

    # avoid ContentType related field accessor clash (an error emitted by model validation)
    #: The model field that stores the :class:`~django.contrib.contenttypes.models.ContentType` reference to the actual class.
    polymorphic_ctype: models.ForeignKey[ContentType | None, ContentType | None] = (
        models.ForeignKey(
            ContentType,
            null=True,
            editable=False,
            on_delete=models.CASCADE,
            related_name="polymorphic_%(app_label)s.%(class)s_set+",
        )
    )

    # some applications want to know the name of the fields that are added to its models
    polymorphic_internal_model_fields: ClassVar[list[str]] = ["polymorphic_ctype"]

    objects: ClassVar[PolymorphicManager[Self]] = PolymorphicManager()

    class Meta:
        abstract: ClassVar[bool] = True

    @classproperty
    def polymorphic_primary_key_name(cls) -> str:
        """
        The name of the root primary key field of this polymorphic inheritance chain.
        """
        pass

    @classmethod
    def translate_polymorphic_Q_object(cls, q: Q) -> Q:
        return translate_polymorphic_Q_object(cls, q)

    def pre_save_polymorphic(self, using: str = DEFAULT_DB_ALIAS) -> None:
        """
        Make sure the ``polymorphic_ctype`` value is correctly set on this model.

        This method automatically updates the polymorphic_ctype when:
        - The object is being saved for the first time
        - The object is being saved to a different database than it was loaded from

        This ensures cross-database saves work correctly without ForeignKeyViolation.
        """
        pass

    def save(
        self,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        """Calls :meth:`pre_save_polymorphic` and saves the model."""
        pass

    save.alters_data = True  # type: ignore[attr-defined]

    def get_real_instance_class(self) -> type[Self] | None:
        """
        Return the actual model type of the object.

        If a non-polymorphic manager (like base_objects) has been used to
        retrieve objects, then the real class/type of these objects may be
        determined using this method.
        """
        pass



    def get_real_instance(self) -> Self:
        """
        Upcast an object to it's actual type.

        If a non-polymorphic manager (like base_objects) has been used to
        retrieve objects, then the complete object with it's real class/type
        and all fields may be retrieved with this method.

        If the model of the object's actual type does not exist (i.e. its
        ContentType is stale), this method raises a
        :class:`~polymorphic.models.PolymorphicTypeInvalid` exception.

        .. note::
            Each method call executes one db query (if necessary).
            Use the :meth:`~polymorphic.managers.PolymorphicQuerySet.get_real_instances`
            to upcast a complete list in a single efficient query.
        """
        pass

    def delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        """
        Behaves the same as Django's default :meth:`~django.db.models.Model.delete()`,
        but with support for upcasting when ``keep_parents`` is True. When keeping
        parents (upcasting the row) the ``polymorphic_ctype`` fields of the parent rows
        are updated accordingly in a transaction with the child row deletion.
        """
        pass

    delete.alters_data = True  # type: ignore[attr-defined]
