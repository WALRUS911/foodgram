from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class FilterIngredient(FilterSet):
    name = filters.CharFilter(lookup_expr='contains', field_name='name')

    class Meta:
        model = Ingredient
        fields = ('name',)


class FilterRecipe(FilterSet):
    author = filters.NumberFilter(field_name='author__id')
    tags = filters.ModelMultipleChoiceFilter(
        to_field_name='slug',
        field_name='tags__slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'is_in_shopping_cart', 'is_favorited', 'tags')
