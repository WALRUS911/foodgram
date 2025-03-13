from collections import Counter
from base64 import b64decode

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

from users.models import Subscribe

from foodgram.const import (
    COOKING_TIME_MIN,
    COOKING_TIME_MAX,
    INGREDIENT_PRICE_MAX,
    INGREDIENT_PRICE_MIN

)

User = get_user_model()


class Base64ImageFieldDecoder(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserRegistrationSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'password',)


class UserProfileSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'userphoto',)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Subscribe.objects.filter(user=user, author=obj).exists()
        )


class SetUserPhotoSerializer(serializers.ModelSerializer):
    avatar = Base64ImageFieldDecoder()

    class Meta:
        model = User
        fields = ('userphoto',)


class UserSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны',
            )
        ]

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        return data

    def to_representation(self, instance):
        return UserSubscribeRepresentationSerializer(
            instance.author, context=self.context
        ).data


class UserSubscribeRepresentationSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count', 'userphoto',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass
        serializer = RecipeShortSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=INGREDIENT_PRICE_MIN,
        max_value=INGREDIENT_PRICE_MAX
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserProfileSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients', read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False)
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )


class RecipeCreateUpdateDetailSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientInputSerializer(many=True)
    image = Base64ImageFieldDecoder()
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_MIN,
        max_value=COOKING_TIME_MAX
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'ingredients', 'name', 'image', 'text',
                  'cooking_time',)

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Рецепт должен содержать хотя бы 1 ингредиент.'
            })

        ingredient_ids = [
            ingredient['ingredient'].id for ingredient in ingredients
        ]
        ingredient_counts = Counter(ingredient_ids)
        duplicates = [
            str(ingredient_id)
            for ingredient_id, count in ingredient_counts.items()
            if count > 1
        ]

        if duplicates:
            raise serializers.ValidationError({
                'ingredients': (
                    'Ингредиенты не должны дублироваться. '
                    f'Повторяются: {", ".join(duplicates)}'
                )
            })

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'У рецепта должен быть тег.'
            })

        tag_ids = [tag.id for tag in tags]
        tag_counts = Counter(tag_ids)
        duplicate_tag = [
            str(tag_id)
            for tag_id, count in tag_counts.items()
            if count > 1
        ]

        if duplicate_tag:
            raise serializers.ValidationError({
                'tags': (
                    'Теги не должны дублироваться. '
                    f'Повторяются: {", ".join(duplicate_tag)}'
                )
            })
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.assign_ingredients_to_recipe(recipe, ingredients_data)
        return recipe

    def assign_ingredients_to_recipe(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients
        ])

    def to_representation(self, instance):
        return RecipeDetailSerializer(instance, context=self.context).data

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.assign_ingredients_to_recipe(instance, ingredients_data)
        return instance


class BaseRecipeActionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context=self.context
        ).data


class RecipeShoppingCartSerializer(BaseRecipeActionSerializer):
    class Meta(BaseRecipeActionSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в корзине.',
            )
        ]


class FavoriteRecipeSerializer(BaseRecipeActionSerializer):
    class Meta(BaseRecipeActionSerializer.Meta):
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в избранном.',
            )
        ]
