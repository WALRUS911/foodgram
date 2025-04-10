from django.contrib import admin
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Subscribe, Tag)

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'username', 'get_recipes_count',
                    'get_subscribers_count')
    list_filter = ('email', 'username', 'last_name', 'first_name')
    list_display_links = ('username',)
    search_fields = ('email', 'username')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            recipes_count=Count('recipe', distinct=True),
            subscribers_count=Count('subscribing', distinct=True)
        )
        return queryset

    def get_recipes_count(self, obj):
        return obj.recipes_count
    get_recipes_count.short_description = 'Рецептов'
    get_recipes_count.admin_order_field = 'recipes_count'

    def get_subscribers_count(self, obj):
        return obj.subscribers_count
    get_subscribers_count.short_description = 'Подписчиков'
    get_subscribers_count.admin_order_field = 'subscribers_count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'id')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('author__username', 'user__username')
    list_filter = ('user', 'author')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    list_display_links = ('name',)
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_filter = ('name', 'tags', 'author')
    list_display_links = ('name',)
    list_display = ('id', 'favorites_count', 'name', 'author', 'get_image')
    search_fields = ('name', 'author__email', 'author__username')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Добавления в избранное')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Изображение')
    def get_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" />', obj.image.url
            )
        return 'Нет фото рецепта.'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user')
    search_fields = ('recipe__name', 'user__username')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user')
    search_fields = ('recipe__name', 'user__username')
