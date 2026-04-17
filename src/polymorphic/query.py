"""
QuerySet for PolymorphicModel
"""

from __future__ import annotations

import copy
import heapq
from collections import defaultdict
from collections.abc import Collection, Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Any, Generic, cast, overload

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import connections, models
from django.db.models import FilteredRelation, Q
from django.db.models.expressions import Combinable
from django.db.models.query import ModelIterable, QuerySet
from typing_extensions import Self, TypeVar

from .query_translate import (
    translate_polymorphic_field_path,
    translate_polymorphic_filter_definitions_in_args,
    translate_polymorphic_filter_definitions_in_kwargs,
    translate_polymorphic_Q_object,
)
from .utils import concrete_descendants, route_to_ancestor

if TYPE_CHECKING:
    from .models import PolymorphicModel  # noqa: F401

_All = TypeVar("_All", bound="PolymorphicModel", covariant=True)
_Base = TypeVar("_Base", bound="PolymorphicModel", default="PolymorphicModel", covariant=True)

_A = TypeVar("_A", bound="PolymorphicModel")
_B = TypeVar("_B", bound="PolymorphicModel")
_C = TypeVar("_C", bound="PolymorphicModel")
_D = TypeVar("_D", bound="PolymorphicModel")

Polymorphic_QuerySet_objects_per_request: int = 2000
"""
The maximum number of objects requested per db-request by the polymorphic
queryset.iterator() implementation
"""

if TYPE_CHECKING:

    class BasePolymorphicModelIterable(ModelIterable[_All]):
        pass
else:

    class BasePolymorphicModelIterable(ModelIterable):
        pass


class _Inconsistent:
    """
    A marker class indicating that there is a mismatch between the content type
    and the actual class of an object retrieved from the database.
    """

    ...


class PolymorphicModelIterable(BasePolymorphicModelIterable, Generic[_All, _Base]):
    """
    ModelIterable for PolymorphicModel

    Yields real instances if qs.polymorphic_disabled is False,
    otherwise acts like a regular ModelIterable.
    """

    queryset: "PolymorphicQuerySet[_All, _Base]"

    def __iter__(self) -> Iterator[_All]:
        base_iter = super().__iter__()
        if self.queryset.polymorphic_disabled:
            return base_iter
        return self._polymorphic_iterator(base_iter)

    def _polymorphic_iterator(self, base_iter: Iterator[_All]) -> Iterator[_All]:
        """
        Here we do the same as::

            real_results = queryset._get_real_instances(list(base_iter))
            for o in real_results: yield o

        but it requests the objects in chunks from the database,
        with QuerySet.iterator(chunk_size) per chunk
        """
        pass


def transmogrify(cls: type[_All], obj: models.Model) -> _All:
    """
    Upcast a class to a different type without asking questions.
    """
    pass


###################################################################################
# PolymorphicQuerySet


class PolymorphicQuerySet(QuerySet[_All], Generic[_All, _Base]):
    """
    QuerySet for PolymorphicModel

    Contains the core functionality for PolymorphicModel

    Usually not explicitly needed, except if a custom queryset class
    is to be used.
    """

    polymorphic_disabled: bool
    polymorphic_deferred_loading: tuple[set[str], bool]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._iterable_class = PolymorphicModelIterable

        self.polymorphic_disabled = False
        # A parallel structure to django.db.models.query.Query.deferred_loading,
        # which we maintain with the untranslated field names passed to
        # .defer() and .only() in order to be able to retranslate them when
        # retrieving the real instance (so that the deferred fields apply
        # to that queryset as well).
        self.polymorphic_deferred_loading = (set(), True)


    @classmethod
    def as_manager(cls) -> models.Manager[_All]:
        """
        Override base :meth:`~django.db.models.query.QuerySet.as_manager` to return
        a manager extended from :class:`polymorphic.managers.PolymorphicManager`.
        """

        from .managers import PolymorphicManager

        manager = PolymorphicManager[_All, _Base].from_queryset(cls)()
        setattr(manager, "_built_with_as_manager", True)
        return manager

    as_manager.queryset_only = True  # type: ignore[attr-defined]


    def non_polymorphic(self) -> PolymorphicQuerySet[_Base, _Base]:
        """switch off polymorphic behaviour for this query.
        When the queryset is evaluated, only objects of the type of the
        base class used for this query are returned."""
        pass

    @overload
    def instance_of(self, __a: type[_A], /) -> PolymorphicQuerySet[_A, _Base]: ...

    @overload
    def instance_of(
        self, __a: type[_A], __b: type[_B], /
    ) -> PolymorphicQuerySet[_A | _B, _Base]: ...

    @overload
    def instance_of(
        self, __a: type[_A], __b: type[_B], __c: type[_C], /
    ) -> PolymorphicQuerySet[_A | _B | _C, _Base]: ...

    @overload
    def instance_of(
        self, __a: type[_A], __b: type[_B], __c: type[_C], __d: type[_D], /
    ) -> PolymorphicQuerySet[_A | _B | _C | _D, _Base]: ...

    @overload
    def instance_of(self, *args: type["PolymorphicModel"]) -> PolymorphicQuerySet[_All, _Base]: ...

    def instance_of(
        self, *args: type["PolymorphicModel"]
    ) -> PolymorphicQuerySet["PolymorphicModel", _Base]:
        """Filter the queryset to only include the classes in args (and their subclasses)."""
        pass

    def not_instance_of(self, *args: type["PolymorphicModel"]) -> Self:
        """Filter the queryset to exclude the classes in args (and their subclasses)."""
        pass


    def order_by(self, *field_names: str | Combinable) -> Self:
        """translate the field paths in the args, then call vanilla order_by."""
        pass

    @overload
    def defer(self, field: None, /) -> Self: ...
    @overload
    def defer(self, *fields: str) -> Self: ...
    def defer(self, *fields: str | None) -> Self:
        """
        Translate the field paths in the args, then call vanilla defer.

        Also retain a copy of the original fields passed, which we'll need
        when we're retrieving the real instance (since we'll need to translate
        them again, as the model will have changed).
        """
        pass

    def only(self, *fields: str) -> Self:
        """
        Translate the field paths in the args, then call vanilla only.

        Also retain a copy of the original fields passed, which we'll need
        when we're retrieving the real instance (since we'll need to translate
        them again, as the model will have changed).
        """
        pass

    def _polymorphic_add_deferred_loading(self, field_names: Iterable[str]) -> None:
        """
        Follows the logic of django.db.models.query.Query.add_deferred_loading(),
        but for the non-translated field names that were passed to self.defer().
        """
        pass

    def _polymorphic_add_immediate_loading(self, field_names: Iterable[str]) -> None:
        """
        Follows the logic of django.db.models.query.Query.add_immediate_loading(),
        but for the non-translated field names that were passed to self.only()
        """
        pass

    def _process_aggregate_args(self, args: Sequence[Any], kwargs: dict[str, Any]) -> None:
        """for aggregate and annotate kwargs: allow ModelX___field syntax for kwargs, forbid it for args.
        Modifies kwargs if needed (these are Aggregate objects, we translate the lookup member variable)
        """
        pass

    def annotate(self, *args: Any, **kwargs: Any) -> Self:
        """translate the polymorphic field paths in the kwargs, then call vanilla annotate.
        _get_real_instances will do the rest of the job after executing the query."""
        pass

    def aggregate(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """translate the polymorphic field paths in the kwargs, then call vanilla aggregate.
        We need no polymorphic object retrieval for aggregate => switch it off."""
        pass

    # Starting with Django 1.9, the copy returned by 'qs.values(...)' has the
    # same class as 'qs', so our polymorphic modifications would apply.
    # We want to leave values queries untouched, so we set 'polymorphic_disabled'.

    # Since django_polymorphic 'V1.0 beta2', extra() always returns polymorphic results.
    # The resulting objects are required to have a unique primary key within the result set
    # (otherwise an error is thrown).
    # The "polymorphic" keyword argument is not supported anymore.
    # def extra(self, *args, **kwargs):

    def _get_real_instances(self, base_result_objects: Sequence[_All]) -> list[_All]:
        """
        Polymorphic object loader

        Does the same as:

            return [ o.get_real_instance() for o in base_result_objects ]

        but more efficiently.

        The list base_result_objects contains the objects from the executed
        base class query. The class of all of them is self.model (our base model).

        Some, many or all of these objects were not created and stored as
        class self.model, but as a class derived from self.model. We want to re-fetch
        these objects from the db as their original class so we can return them
        just as they were created/saved.

        We identify these objects by looking at o.polymorphic_ctype, which specifies
        the real class of these objects (the class at the time they were saved).

        First, we sort the result objects in base_result_objects for their
        subclass (from o.polymorphic_ctype), and then we execute one db query per
        subclass of objects. Here, we handle any annotations from annotate().

        Finally we re-sort the resulting objects into the correct order and
        return them as a list.
        """
        pass

    def __repr__(self, *args, **kwargs):
        if self.model.polymorphic_query_multiline_output:
            result = ",\n  ".join(repr(o) for o in self.all())
            return f"[ {result} ]"
        else:
            return super().__repr__(*args, **kwargs)

    class _p_list_class(list[Any]):
        def __repr__(self, *args: Any, **kwargs: Any) -> str:
            result = ",\n  ".join(repr(o) for o in self)
            return f"[ {result} ]"

    def get_real_instances(self, base_result_objects: Iterable[_All] | None = None) -> list[_All]:
        """
        Cast a list of objects to their actual classes.

        This does roughly the same as::

            return [ o.get_real_instance() for o in base_result_objects ]

        but more efficiently.

        :rtype: PolymorphicQuerySet
        """
        pass

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Deletion will be done non-polymorphically because Django's multi-table deletion
        mechanism is already walking the class hierarchy and producing a correct
        deletion graph. Introducing polymorphic querysets into the deletion process
        disrupts the model hierarchy/relationship traversal.
        """
        pass
