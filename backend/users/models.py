from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram.const import MAX_LENGTH


class CustomUser(AbstractUser):

    username = models.CharField(
        max_length=MAX_LENGTH,
        validators=[UnicodeUsernameValidator()],
        verbose_name='Логин',
        unique=True,
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='E-mail',
    )
    userphoto = models.ImageField(
        upload_to='user_photo/',
        verbose_name='Фото пользователя',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('author',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_subscription',
            )
        ]

    def __str__(self):
        return f"{self.user} на  {self.author}"
