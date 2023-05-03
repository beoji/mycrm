from django.urls import path
from . import views


app_name = 'korespondencja'
urlpatterns = [
    # Korespondencja
    path('', views.KorespondencjaList.as_view(), name='korespondencja-list'),
    path('create/', views.KorespondencjaCreate.as_view(), name='korespondencja-create'),
    path('<int:pk>/', views.KorespondencjaDetail.as_view(), name='korespondencja-detail'),
    path('<int:pk>/update/', views.KorespondencjaUpdate.as_view(), name='korespondencja-update'),
    path('<int:pk>/delete/', views.KorespondencjaDelete.as_view(), name='korespondencja-delete'),

    # Nadawca/odbiorca
    path('kontakt/', views.KontaktList.as_view(), name='kontakt-list'),
    path('kontakt/<int:pk>/', views.KontaktDetail.as_view(), name='kontakt-detail'),
    path('kontakt/<int:pk>/update/', views.KontaktUpdate.as_view(), name='kontakt-update'),
    path('kontakt/<int:pk>/delete/', views.KontaktDelete.as_view(), name='kontakt-delete'),

    # Ajax helper
    path('personhelper/', views.personhelper, name='personhelper'),
    path('getrecievers/', views.getrecievers, name='getrecievers'),
    path('getmailbydate/', views.get_mail_by_date, name='getmailbydate'),
]
