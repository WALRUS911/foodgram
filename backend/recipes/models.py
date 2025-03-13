from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram.const import (
    MAX_LENGTH,
    INGREDIENT_PRICE_MAX,
    INGREDIENT_PRICE_MIN,
    RECIPE_MAX_LENGTH,
    COOKING_TIME_MIN,
    COOKING_TIME_MAX
)


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=RECIPE_MAX_LENGTH,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(COOKING_TIME_MIN),
                    MaxValueValidator(COOKING_TIME_MAX)],
        verbose_name='Время приготовления',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(INGREDIENT_PRICE_MIN),
                    MaxValueValidator(INGREDIENT_PRICE_MAX)],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ('id',)

    def __str__(self):
        return (f'{self.recipe.name}: {self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='user_favorite',
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} пользователем {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='carts',
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='carts',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='user_shoppingcart',
            )
        ]

    def __str__(self):
        return f'{self.recipe} пользователем {self.user}'
