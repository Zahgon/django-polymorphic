from typing import Any, cast

from django.db.models import QuerySet
from django.db.models.fields.related_descriptors import (
    ForwardOneToOneDescriptor,
    ReverseOneToOneDescriptor,
)


class NonPolymorphicForwardOneToOneDescriptor(ForwardOneToOneDescriptor):
    """
    A custom descriptor for forward OneToOne relations to polymorphic models that
    returns non-polymorphic instances. This is used for the parent to child links
    in multi-table polymorphic models.
    """



class NonPolymorphicReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
    """
    A custom descriptor for reverse OneToOne relations to polymorphic models that
    returns non-polymorphic instances. This is used for the child to parent links
    in multi-table polymorphic models.
    """

