from django.core.management.base import BaseCommand
from django.db.models import Q

from recipes.models import Tag

TAGS = [
    ('Завтрак', 'breakfast',),
    ('Обед', 'lunch',),
    ('Ужин', 'dinner',)
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        for tag in TAGS:
            if Tag.objects.filter(
                Q(name=tag[0]) | Q(slug=tag[1])
            ).exists():
                self.stdout.write(
                    self.style.ERROR(f'{tag[0]!r} уже существует!')
                )
                continue
            Tag.objects.create(name=tag[0], slug=tag[1])
            self.stdout.write(
                self.style.SUCCESS(f'Успешно добавлен {tag[0]!r}')
            )
