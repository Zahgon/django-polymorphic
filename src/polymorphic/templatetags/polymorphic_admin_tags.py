from django.template import Context, Library, Node, NodeList, TemplateSyntaxError
from django.template.base import FilterExpression, Parser, Token
from typing_extensions import Self

register: Library = Library()


class BreadcrumbScope(Node):
    base_opts: FilterExpression
    nodelist: NodeList

    def __init__(self, base_opts: FilterExpression, nodelist: NodeList) -> None:
        self.base_opts = base_opts
        self.nodelist = nodelist  # Note, takes advantage of Node.child_nodelists




@register.tag
def breadcrumb_scope(parser: Parser, token: Token) -> BreadcrumbScope:
    """
    .. templatetag:: breadcrumb_scope

    Easily allow the breadcrumb to be generated in the admin change templates.

    The ``{% breadcrumb_scope ... %}`` tag makes sure the ``{{ opts }}`` and
    ``{{ app_label }}`` values are temporary based on the provided
    ``{{ base_opts }}``.

    This allows fixing the breadcrumb in admin templates:

    .. code-block:: html+django

        {% extends "admin/change_form.html" %}
        {% load polymorphic_admin_tags %}

        {% block breadcrumbs %}
        {% breadcrumb_scope base_opts %}{{ block.super }}{% endbreadcrumb_scope %}
        {% endblock %}
    """
    pass
