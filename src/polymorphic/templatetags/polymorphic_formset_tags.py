"""
.. versionadded:: 1.1

To render formsets in the frontend, the ``polymorphic_tags`` provides extra
filters to implement HTML rendering of polymorphic formsets.

The following filters are provided;

* ``{{ formset|as_script_options }}`` render the ``data-options`` for a JavaScript formset library.
* ``{{ formset|include_empty_form }}`` provide the placeholder form for an add button.
* ``{{ form|as_form_type }}`` return the model name that the form instance uses.
* ``{{ model|as_model_name }}`` performs the same, for a model class or instance.

.. code-block:: html+django

    {% load i18n polymorphic_formset_tags %}

    <div class="inline-group" id="{{ formset.prefix }}-group" data-options="{{ formset|as_script_options }}">
        {% block add_button %}
            {% if formset.show_add_button|default_if_none:'1' %}
                {% if formset.empty_forms %}
                    {# django-polymorphic formset (e.g. PolymorphicInlineFormSetView) #}
                    <div class="btn-group" role="group">
                      {% for model in formset.child_forms %}
                          <a type="button" data-type="{{ model|as_model_name }}" class="js-add-form btn btn-default">{% glyphicon 'plus' %} {{ model|as_verbose_name }}</a>
                      {% endfor %}
                    </div>
                {% else %}
                    <a class="btn btn-default js-add-form">{% trans "Add" %}</a>
                {% endif %}
            {% endif %}
        {% endblock %}

        {{ formset.management_form }}

        {% for form in formset|include_empty_form %}
          {% block formset_form_wrapper %}
            <div id="{{ form.prefix }}" data-inline-type="{{ form|as_form_type|lower }}" class="inline-related{% if '__prefix__' in form.prefix %} empty-form{% endif %}">
                {{ form.non_field_errors }}

                {# Add the 'pk' field that is not mentioned in crispy #}
                {% for field in form.hidden_fields %}
                  {{ field }}
                {% endfor %}

                {% block formset_form %}
                    {% crispy form %}
                {% endblock %}
            </div>
          {% endblock %}
        {% endfor %}
    </div>
"""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, cast

from django.db import models
from django.forms import BaseForm, BaseFormSet
from django.template import Library
from django.utils.encoding import force_str
from django.utils.text import capfirst
from django.utils.translation import gettext

from polymorphic.formsets import BasePolymorphicModelFormSet

if TYPE_CHECKING:
    from django.forms import BaseModelFormSet, ModelForm

register: Library = Library()


@register.filter()
def include_empty_form(formset: BaseFormSet) -> Generator[BaseForm, None, None]:
    """
    .. templatetag:: include_empty_form

    Make sure the "empty form" is included when displaying a formset (typically table with input rows)
    """
    pass


@register.filter
def as_script_options(formset: "BaseModelFormSet[Any, Any]") -> str:
    """
    .. templatetag:: as_script_options

    A JavaScript data structure for the JavaScript code

    This generates the ``data-options`` attribute for ``jquery.django-inlines.js``
    The formset may define the following extra attributes:

    - ``verbose_name``
    - ``add_text``
    - ``show_add_button``
    """
    pass


@register.filter
def as_form_type(form: "ModelForm[Any]") -> str:
    """
    .. templatetag:: as_form_type

    Usage: ``{{ form|as_form_type }}``
    """
    pass


@register.filter
def as_model_name(model: type[models.Model]) -> str:
    """
    .. templatetag:: as_model_name

    Usage: ``{{ model|as_model_name }}``
    """
    pass
