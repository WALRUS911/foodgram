from base64 import b64decode

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscribe, Tag)
from foodgram.const import (
    AMOUNT_MIN,
    AMOUNT_MAX,
    TIME_COOK_VALUE_MIN,
    TIME_COOK_VALUE_MAX
)

User = get_user_model()


class Base64ImageFieldDecoder(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializerReg(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'last_name',
                  'first_name', 'email', 'password',)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageFieldDecoder()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializerSubscribe(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                message='Вы уже подписаны',
                queryset=Subscribe.objects.all(),
                fields=('author', 'user'),
            )
        ]

    def to_representation(self, instance):
        return UserSerializerSubscribeRepresentation(
            instance.author, context=self.context
        ).data

    def validate(self, data):
        author = data['author']
        user = self.context['request'].user
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        return data


class UserSerializerProfile(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'avatar', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.subscribing.filter(user=user).exists()
        )


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')


class UserSerializerSubscribeRepresentation(UserSerializerProfile):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta:
        model = User
        fields = ('email', 'avatar', 'id', 'first_name', 'last_name',
                  'username', 'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass
        serializer = ShortRecipeSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class SerializerRecipeIngredientInput(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN,
        max_value=AMOUNT_MAX
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


class DetailRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializerProfile(read_only=True)
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
            'id', 'author', 'tags', 'ingredients', 'is_favorited',
            'name', 'image', 'is_in_shopping_cart', 'text', 'cooking_time',
        )


class SerializerBaseRecipeAction(serializers.ModelSerializer):
    class Meta:
        fields = ('recipe', 'user')

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context
        ).data


class SerializerRecipeCreateUpdate(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = SerializerRecipeIngredientInput(many=True)
    image = Base64ImageFieldDecoder()
    cooking_time = serializers.IntegerField(
        min_value=TIME_COOK_VALUE_MIN,
        max_value=TIME_COOK_VALUE_MAX
    )

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'ingredients', 'image', 'text',
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
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальными.'
            })

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'У рецепта должен  быть хотя бы 1 тег.'
            })

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги должны быть уникальными.'
            })
        return data

    def assign_ingredients_to_recipe(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.assign_ingredients_to_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self.assign_ingredients_to_recipe(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        return DetailRecipeSerializer(instance, context=self.context).data


class SerializerFavoriteRecipe(SerializerBaseRecipeAction):
    class Meta(SerializerBaseRecipeAction.Meta):
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                message='Этот рецепт уже добавлено в избранное.',
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
            )
        ]


class SerializerRecipeShoppingCart(SerializerBaseRecipeAction):
    class Meta(SerializerBaseRecipeAction.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                message='Этот рецепт уже в корзине.',
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
            )
        ]
