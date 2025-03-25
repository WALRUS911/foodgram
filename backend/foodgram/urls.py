from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from recipes.models import Recipe


def short_link_redirect(request, encoded_id):
    try:
        decoded_id = force_str(urlsafe_base64_decode(encoded_id))
        recipe_id = int(decoded_id)
        get_object_or_404(Recipe, id=recipe_id)
        return HttpResponseRedirect(f'/recipes/{recipe_id}/')
    except (ValueError, TypeError):
        return HttpResponse(status=404)


urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path(
        's/<str:encoded_id>/',
        short_link_redirect,
        name='short_link_redirect'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
