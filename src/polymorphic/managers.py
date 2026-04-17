"""
The manager class for use in the models.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeAlias, cast, overload

from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, models, transaction
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from typing_extensions import Self, TypeVar

from polymorphic.query import PolymorphicQuerySet

if TYPE_CHECKING:
    from .models import PolymorphicModel  # noqa: F401


__all__ = [
    "PolymorphicManager",
    "PolymorphicQuerySet",
    "PolymorphicManyToManyDescriptor",
    "PolymorphicReverseManyToOneDescriptor",
    "PolymorphicForwardManyToOneDescriptor",
    "PolymorphicForwardOneToOneDescriptor",
    "PolymorphicReverseOneToOneDescriptor",
    "Nullable",
]

_All = TypeVar("_All", bound="PolymorphicModel", covariant=True)
"""
This :class:`~typing.TypeVar` represents the union of all possible polymorphic types
that a manager may return. All models must derive from
:class:`~polymorphic.models.PolymorphicModel`
"""

_Base = TypeVar("_Base", bound="PolymorphicModel", default="PolymorphicModel", covariant=True)
"""
This :class:`~typing.TypeVar` represents the base model type from which polymorphic
models derive. For managers on a :class:`~polymorphic.models.PolymorphicModel` subclass,
you will likely want to use :data:`~typing.Self`.
"""

_Through = TypeVar("_Through", bound=models.Model, default=models.Model, covariant=True)
"""
This :class:`~typing.TypeVar` represents the "through" model type for many-to-many
relations. By default it is just a regular :class:`~django.db.models.Model`, which
will lack the foreign key relations to the linked models.
"""

_Nullable = TypeVar("_Nullable", Literal[True], Literal[False], default=Literal[False])
"""
Provided for nullable relations - should be set to ``Literal[True]`` if the relation is
nullable, otherwise can be left as the default ``Literal[False]``.
"""

_A = TypeVar("_A", bound="PolymorphicModel")
_B = TypeVar("_B", bound="PolymorphicModel")
_C = TypeVar("_C", bound="PolymorphicModel")
_D = TypeVar("_D", bound="PolymorphicModel")


Nullable: TypeAlias = Literal[True]
"""A more readable type hint alias to indicate that a relation is nullable."""


class PolymorphicManager(models.Manager[_All], Generic[_All, _Base]):
    """
    Manager for PolymorphicModel

    Usually not explicitly needed, except if a custom manager or
    a custom queryset class is to be used.
    """

    queryset_class: type[PolymorphicQuerySet[_All, _Base]] = PolymorphicQuerySet

    if TYPE_CHECKING:

        def all(self) -> PolymorphicQuerySet[_All, _Base]: ...
        def filter(self, *args: Any, **kwargs: Any) -> PolymorphicQuerySet[_All, _Base]: ...

    @classmethod
    def from_queryset(
        cls, queryset_class: type[models.query.QuerySet[_All]], class_name: str | None = None
    ) -> type[Self]:
        manager = super().from_queryset(queryset_class, class_name=class_name)
        # also set our version, Django uses _queryset_class
        manager.queryset_class = queryset_class  # type: ignore[assignment]
        return manager


    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} (PolymorphicManager) using {self.queryset_class.__name__}"
        )

    # Proxied methods

    # fixme: remove overloads when/if typing ever supports variadic generic unions
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
    def instance_of(self, *args: type[PolymorphicModel]) -> PolymorphicQuerySet[_All, _Base]: ...




    def create_from_super(self, obj: models.Model, **kwargs: Any) -> _Base:
        """
        Create an instance of this manager's model class from the given instance of a
        parent class.

        This is useful when "promoting" an instance down the inheritance chain.

        :param obj: An instance of a parent class of the manager's model class.
        :param kwargs: Additional fields to set on the new instance.
        :return: The newly created instance.
        """
        pass


if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import (
        ManyRelatedManager,
        RelatedManager,
    )

    class PolymorphicManyRelatedManager(  # type: ignore[type-var]
        PolymorphicManager[_All, _Base],
        ManyRelatedManager[_All, _Through],  # pyright: ignore[reportInvalidTypeArguments]
        Generic[_All, _Base, _Through],
    ): ...

    class PolymorphicRelatedManager(  # type: ignore[type-var]
        PolymorphicManager[_All, _Base],
        RelatedManager[_All],  # pyright: ignore[reportInvalidTypeArguments]
        Generic[_All, _Base],
    ): ...

else:

    class PolymorphicRelatedManager(PolymorphicManager[_All, _Base], Generic[_All, _Base]): ...

    class PolymorphicManyRelatedManager(
        PolymorphicManager[_All, _Base],
        Generic[_All, _Base, _Through],
    ): ...


class PolymorphicManyToManyDescriptor(ManyToManyDescriptor, Generic[_All, _Base, _Through]):
    """
    Use this descriptor class as a type hint for your forward and reverse
    :class:`~django.db.models.ManyToManyField` relations to/from polymorphic models.
    For example:

    .. code-block:: python

        to_parents: PolymorphicManyToManyDescriptor[
            ParentModel | Child1 | Child2,  # all possible polymorphic types
            ParentModel,                    # the base type (for non_polymorphic)
            ThroughModel                    # if custom through model
        ] = models.ManyToManyField(         # type: ignore[assignment]
            "ParentModel",
            related_name="to_parents_reverse"
        )

    """

    @overload  # type: ignore[override]
    def __get__(self, instance: None, cls: Any | None = None, /) -> Self: ...

    @overload
    def __get__(
        self, instance: models.Model, cls: Any | None = None, /
    ) -> PolymorphicManyRelatedManager[_All, _Base, _Through]: ...

    def __get__(
        self, instance: models.Model | None, cls: Any | None = None, /
    ) -> Self | PolymorphicManyRelatedManager[_All, _Base, _Through]:
        return cast(  # pragma: no cover
            Self | PolymorphicManyRelatedManager[_All, _Base, _Through],
            super().__get__(instance, cls),
        )


class PolymorphicReverseManyToOneDescriptor(
    ReverseManyToOneDescriptor,
    Generic[_All, _Base],
):
    """
    Use this descriptor class as a type hint for your reverse
    :class:`~django.db.models.ForeignKey` relations to polymorphic models. For example:


    .. code-block:: python

        class ParentModel(PolymorphicModel):
            models.ForeignKey(
                RelatedModel,
                on_delete=models.CASCADE,
                null=True,
                related_name="reverse"
            )

        class RelatedModel(models.Model):

            reverse: PolymorphicReverseManyToOneDescriptor[
                ParentModel | Child1 | Child2,
                ParentModel
            ]
    """

    @overload
    def __get__(self, instance: None, cls: Any | None = None, /) -> Self: ...

    @overload
    def __get__(
        self, instance: models.Model, cls: Any | None = None, /
    ) -> PolymorphicRelatedManager[_All, _Base]: ...

    def __get__(
        self, instance: models.Model | None, cls: Any | None = None, /
    ) -> Self | PolymorphicRelatedManager[_All, _Base]:
        return cast(  # pragma: no cover
            Self | PolymorphicRelatedManager[_All, _Base], super().__get__(instance, cls)
        )


class PolymorphicForwardManyToOneDescriptor(
    ForwardManyToOneDescriptor,
    Generic[_All, _Base, _Nullable],
):
    """
    Use this descriptor class as a type hint for your
    :class:`~django.db.models.ForeignKey` relations to polymorphic models. For example:

    .. note::

        Your typing system will likely flag an assignment error on the class attribute
        - this is unfortunate but unavoidable - we suggest you add a
        `# type: ignore[assignment]`.

    .. code-block:: python

        parent: PolymorphicForwardManyToOneDescriptor[
            ParentModel | Child1 | Child2,
            ParentModel,
            Nullable,
        ] = models.ForeignKey(
            ParentModel,
            on_delete=models.CASCADE,
            null=True,
        )
    """

    @overload  # type: ignore[override]
    def __get__(self, instance: None, cls: Any | None = None, /) -> Self: ...

    @overload
    def __get__(
        self: PolymorphicForwardManyToOneDescriptor[_All, _Base, Literal[False]],
        instance: models.Model,
        cls: Any | None = None,
        /,
    ) -> _All: ...

    @overload
    def __get__(
        self: PolymorphicForwardManyToOneDescriptor[_All, _Base, Literal[True]],
        instance: models.Model,
        cls: Any | None = None,
        /,
    ) -> _All | None: ...

    def __get__(
        self, instance: models.Model | None, cls: Any | None = None, /
    ) -> Self | _All | None:
        return cast(  # pragma: no cover
            Self | _All | None, super().__get__(instance, cls)
        )



class PolymorphicForwardOneToOneDescriptor(
    ForwardOneToOneDescriptor,
    PolymorphicForwardManyToOneDescriptor[_All, _Base, _Nullable],
    Generic[_All, _Base, _Nullable],
):
    """
    Use this descriptor class as a type hint for your
    :class:`~django.db.models.OneToOneField` relations to polymorphic models. For
    example:

    .. note::

        Your typing system will likely flag an assignment error on the class attribute
        - this is unfortunate but unavoidable - we suggest you add a
        `# type: ignore[assignment]`.

    .. code-block:: python

        parent: PolymorphicForwardOneToOneDescriptor[
            ParentModel | Child1 | Child2,
            ParentModel,
            Nullable,
        ] = models.OneToOneField(
            ParentModel,
            on_delete=models.CASCADE,
            null=True,
        )
    """


class PolymorphicReverseOneToOneDescriptor(
    ReverseOneToOneDescriptor,
    Generic[_All, _Base, _Nullable],
):
    """
    Use this descriptor class as a type hint for your reverse
    :class:`~django.db.models.OneToOneField` relations to polymorphic models. For
    example:

    .. code-block:: python

        class ParentModel(PolymorphicModel):
            models.OneToOneField(
                RelatedModel,
                on_delete=models.CASCADE,
                null=True,
                related_name="reverse"
            )

        class RelatedModel(models.Model):

            reverse: PolymorphicReverseOneToOneDescriptor[
                ParentModel | Child1 | Child2,
                ParentModel,
                Nullable,
            ]
    """

    @overload
    def __get__(self, instance: None, cls: Any | None = None, /) -> Self: ...

    @overload
    def __get__(
        self: PolymorphicReverseOneToOneDescriptor[_All, _Base, Literal[False]],
        instance: models.Model,
        cls: Any | None = None,
        /,
    ) -> _All: ...

    @overload
    def __get__(
        self: PolymorphicReverseOneToOneDescriptor[_All, _Base, Literal[True]],
        instance: models.Model,
        cls: Any | None = None,
        /,
    ) -> _All | None: ...

    def __get__(
        self, instance: models.Model | None, cls: Any | None = None, /
    ) -> Self | _All | None:
        return cast(  # pragma: no cover
            Self | _All | None, super().__get__(instance, cls)
        )

