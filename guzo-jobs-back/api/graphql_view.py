from django.contrib.auth.models import AnonymousUser
from graphene.validation import depth_limit_validator
from graphene_django.views import GraphQLView
from graphql import GraphQLError, specified_rules
from graphql.validation import ValidationRule


class FieldBudget(ValidationRule):
    def __init__(self, context):
        super().__init__(context)
        self.fields = 0

    def enter_field(self, node, *_args):
        self.fields += 1
        if self.fields == 201:
            self.report_error(GraphQLError('Query exceeds the 200-field budget.', node))

    def enter_operation_definition(self, node, *_args):
        fragments = {definition.name.value: definition for definition in self.context.document.definitions if definition.kind == 'fragment_definition'}
        count = 0

        def visit(selection_set, path=()):
            nonlocal count
            if selection_set is None:
                return
            for selection in selection_set.selections:
                count += 1
                if count > 1000 or len(path) > 12:
                    raise ValueError()
                if selection.kind == 'fragment_spread':
                    name = selection.name.value
                    if name in path:
                        raise ValueError()
                    if name in fragments:
                        visit(fragments[name].selection_set, (*path, name))
                else:
                    visit(getattr(selection, 'selection_set', None), path)

        try:
            visit(node.selection_set)
        except ValueError:
            self.report_error(GraphQLError('Expanded query exceeds the work budget.', node))


class BoundedGraphQLView(GraphQLView):
    validation_rules = (*specified_rules, depth_limit_validator(max_depth=12), FieldBudget)

    def dispatch(self, request, *args, **kwargs):
        # This CSRF-exempt endpoint accepts explicit bearer tokens, never admin session cookies.
        request.user = AnonymousUser()
        return super().dispatch(request, *args, **kwargs)
