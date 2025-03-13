from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeCreateUpdateDetailSerializer,
                          RecipeDetailSerializer,
                          RecipeShoppingCartSerializer, SetUserPhotoSerializer,
                          TagSerializer, UserProfileSerializer,
                          UserSubscribeRepresentationSerializer,
                          UserSubscribeSerializer)
from .permissions import IsAdminAuthorOrReadOnly


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=('get',)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=('get',)
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribing__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserSubscribeRepresentationSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('post',)
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        data = {'author': author.id, 'user': request.user.id}
        serializer = UserSubscribeSerializer(
            context={'request': request},
            data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        deleted, _ = request.user.subscriber.filter(author=author).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError('Вы не подписаны на пользователя.')

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/userphoto',
    )
    def set_avatar(self, request):
        serializer = SetUserPhotoSerializer(
            instance=request.user, data=request.data, context={
                'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAdminAuthorOrReadOnly,)
    http_method_names = ['post', 'get', 'patch', 'delete']

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'recipe_ingredients__ingredient', 'tags'
        )

        if user_id:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    self.request.user.favorites.filter(recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    self.request.user.carts.filter(recipe=OuterRef('pk'))
                )
            )
        else:
            queryset = queryset.annotate(
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
                is_favorited=Value(False, output_field=BooleanField())

            )

        return queryset

    def add_recipe_to(self, model, serializer_class, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = serializer_class(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeDetailSerializer
        return RecipeCreateUpdateDetailSerializer

    def remove_recipe_from(self, model, request, pk, error_message):
        recipe = get_object_or_404(Recipe, id=pk)
        instance = model.objects.filter(user=request.user, recipe=recipe)
        deleted, _ = instance.delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError(error_message)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('post',)
    )
    def favorite(self, request, pk=None):
        return self.add_recipe_to(
            Favorite, FavoriteRecipeSerializer, request, pk
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        error_message = 'Рецепта нет в избранном.'
        return self.remove_recipe_from(Favorite, request, pk, error_message)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=('post',)
    )
    def shopping_cart(self, request, pk=None):
        return self.add_recipe_to(
            ShoppingCart, RecipeShoppingCartSerializer, request, pk
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        error_message = 'Рецепт отсутствует в списке покупок.'
        return self.remove_recipe_from(
            ShoppingCart, request, pk, error_message
        )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=('get',)
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__carts__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients.exists():
            raise ValidationError('Список покупок пуст.')

        shopping_list = f'Список покупок для {user.get_full_name()} :\n\n'
        for item in ingredients:
            shopping_list += (
                f'{item["ingredient__name"]} '
                f'({item["ingredient__measurement_unit"]}) — '
                f'{item["amount"]}\n'
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        url_path='get-link',
        methods=('get',)
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        encoded_id = urlsafe_base64_encode(force_bytes(recipe.id))
        short_link = request.build_absolute_uri(f'/s/{encoded_id}/')
        return Response({'short-link': short_link})
