from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.core.exceptions import ValidationError
from django.db.models import Q


from foodgram.const import (
    MAX_LENGTH_NAME,
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_TAG_MAX,
    MAX_LENGTH_TAG_SLUG,
    MAX_LENGTH_INGREDIENT,
    MAX_LENGTH_INGREDIENT_UNIT,
    AMOUNT_MIN,
    AMOUNT_MAX,
    MAX_LENGTH_NAME_RECIPE,
    TIME_COOK_VALUE_MIN,
    TIME_COOK_VALUE_MAX
)


class Subscribe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Подписчик',
        related_name='subscriber',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscribing',
    )

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'
        ordering = ('author',)
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'user',),
                name='user_author_subscription',
            ),
            # Запрет подписки на самого себя
            models.CheckConstraint(
                check=~Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return f"{self.user} на автора {self.author}"

    def clean(self):
        """Валидация на уровне приложения"""
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        super().clean()


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Логин',
        unique=True,
        max_length=MAX_LENGTH_NAME,
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        verbose_name='E-mail',
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_NAME,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_NAME,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Аватар',
        blank=True,
        default='',
    )

    REQUIRED_FIELDS = ['username', 'last_name', 'first_name', 'password']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_MAX,
        verbose_name='Название',
        unique=True,
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        verbose_name='Слаг',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        ordering = ('name',)
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_INGREDIENT,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH_INGREDIENT_UNIT,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        ordering = ('name',)
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_measurement'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=MAX_LENGTH_NAME_RECIPE,

    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(TIME_COOK_VALUE_MIN),
                    MaxValueValidator(TIME_COOK_VALUE_MAX)],
    )

    class Meta:
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'
        ordering = ('name',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(AMOUNT_MIN),
                    MaxValueValidator(AMOUNT_MAX)],
    )

    class Meta:
        verbose_name_plural = 'Ингредиенты в рецепте'
        verbose_name = 'Ингредиент в рецепте'
        ordering = ('ingredient',)
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient_pair'
            )
        ]

    def __str__(self):
        return (f'{self.recipe.name}: {self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')


class UserRecipeBaseModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique'  # Автогенерация имени
            )
        ]

    def __str__(self):
        return f'{self.recipe} | {self.user}'


class Favorite(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'


class ShoppingCart(UserRecipeBaseModel):
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        default_related_name = 'shopping_carts'
