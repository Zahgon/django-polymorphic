from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from rest_framework import serializers
from rest_framework.fields import empty


class PolymorphicSerializer(serializers.Serializer):
    model_serializer_mapping: dict[models.Model, serializers.Serializer]
    resource_type_field_name = "resourcetype"

    def __new__(cls, *args, **kwargs):
        if getattr(cls, "model_serializer_mapping", None) is None:
            raise ImproperlyConfigured(
                "`{cls}` is missing a `{cls}.model_serializer_mapping` attribute".format(
                    cls=cls.__name__
                )
            )
        if not isinstance(cls.resource_type_field_name, str):
            raise ImproperlyConfigured(
                "`{cls}.resource_type_field_name` must be a string".format(cls=cls.__name__)
            )
        return super(PolymorphicSerializer, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

        model_serializer_mapping = self.model_serializer_mapping
        self.model_serializer_mapping = {}
        self.resource_type_model_mapping = {}

        for model, serializer in model_serializer_mapping.items():
            resource_type = self.to_resource_type(model)
            if callable(serializer):
                serializer = serializer(*args, **kwargs)
                serializer.parent = self

            self.resource_type_model_mapping[resource_type] = model
            self.model_serializer_mapping[model] = serializer

    # ----------
    # Public API





    def update(self, instance, validated_data):
        resource_type = validated_data.pop(self.resource_type_field_name)
        serializer = self._get_serializer_from_resource_type(resource_type)
        return serializer.update(instance, validated_data)



    # --------------
    # Implementation

    def _to_model(self, model_or_instance):
        return (
            model_or_instance.__class__
            if isinstance(model_or_instance, models.Model)
            else model_or_instance
        )


    def _get_serializer_from_model_or_instance(self, model_or_instance):
        model = self._to_model(model_or_instance)

        for klass in model.mro():
            if klass in self.model_serializer_mapping:
                return self.model_serializer_mapping[klass]

        raise KeyError(
            "`{cls}.model_serializer_mapping` is missing "
            "a corresponding serializer for `{model}` model".format(
                cls=self.__class__.__name__, model=model.__name__
            )
        )

    def _get_serializer_from_resource_type(self, resource_type):
        try:
            model = self.resource_type_model_mapping[resource_type]
        except KeyError:
            raise serializers.ValidationError(
                {
                    self.resource_type_field_name: "Invalid {0}".format(
                        self.resource_type_field_name
                    )
                }
            )

        return self._get_serializer_from_model_or_instance(model)
