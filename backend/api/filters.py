from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        to_field_name='slug',
        field_name='tags__slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    author = filters.NumberFilter(field_name='author__id')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited')


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='contains')

    class Meta:
        model = Ingredient
        fields = ('name',)
