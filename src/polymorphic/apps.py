from typing import Any, Iterable, Sequence

from django.apps import AppConfig, apps
from django.core.checks import CheckMessage, Error, Tags, Warning, register
from django.db import models


@register(Tags.models)
def check_reserved_field_names(
    app_configs: Sequence[AppConfig] | None, **kwargs: Any
) -> Iterable[CheckMessage]:
    """
    System check that ensures models don't use reserved field names.
    """
    pass






class PolymorphicConfig(AppConfig):
    name: str = "polymorphic"
    verbose_name: str = "Django Polymorphic"

    def ready(self) -> None:
        pass
