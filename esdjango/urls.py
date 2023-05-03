from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('password_reset/', views.reset_denied),
    # url(r'^password_reset/done/$', views.reset_denied),
    path('reset/', views.reset_denied),
    # url(r'^reset/done/$', views.reset_denied),
    path('password_change/', views.change_password),
    path('', include('django.contrib.auth.urls')),
    path('escrm/', include('escrm.urls')),
    path('admin/', admin.site.urls),
    path('accounts/profile/', views.cust_login),
    path('platnosci/', include('platnosci.urls')),
    path('korespondencja/', include('korespondencja.urls')),
    path('profil/', views.profil, name='profil'),
    path('profil/edit/', views.update_profile, name='profil-edit'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
