from django.urls import path
from . import views

app_name = 'escrm'

urlpatterns = [
    path('', views.CrmDashboard.as_view(), name='escrm-dashboard'),
    # dokumenty
    path('dokument/<int:pk>/', views.dokument_get, name='dokument-download'),
    path('dokument/<int:pk>/delete', views.DokumentDelete.as_view(), name='dokument-delete'),
    path('dokument/<int:pk>/add', views.dokument_add, name='dokument-add'),

    # Zarządzanie kontrahentami
    path('kontrahent/', views.KontrahentList.as_view(), name='kontrahent-list'),
    path('kontrahent/create/', views.KontrahentCreate.as_view(), name='kontrahent-create'),
    path('kontrahent/<int:pk>/', views.KontrahentDetail.as_view(), name='kontrahent-detail'),
    path('kontrahent/<int:pk>/update/', views.KontrahentUpdate.as_view(), name='kontrahent-update'),
    path('kontrahent/<int:pk>/delete/', views.KontrahentDelete.as_view(), name='kontrahent-delete'),
    path('kontrahent/<int:pk>/take/', views.kontrahent_take, name='kontrahent-take'),
    path('kontrahent/<int:pk>/dashboard/', views.kontrahent_dashboard, name='kontrahent-dashboard'),

    # Zarządzanie adresami
    path('kontrahent/set-default-adress/<int:pk>', views.default_check, name='default-check'),
    path('kontrahent/adres/create', views.adres_kontrahent_create, name='adres-kontrahent-create'),
    path('kontrahent/adres/update/get', views.adres_kontrahent_update, name='adres-kontrahent-update-get'),
    path('kontrahent/adres/<int:pk>/update/save', views.adres_kontrahent_update_saving, name='adres-kontrahent-update-save'),
    path('kontrahent/adres/<int:pk>/delete/', views.adres_kontrahent_delete, name='adres-kontrahent-delete'),

    # Zarządzanie osobami
    path('osoba/create/', views.osoba_create, name='osoba-create'),
    path('osoba/update/get', views.osoba_update, name='osoba-update-get'),
    path('osoba/<int:pk>/', views.OsobaDetail.as_view(), name='osoba-detail'),
    path('osoba/<int:pk>/update/save', views.osoba_update_saving, name='osoba-update-save'),
    path('osoba/<int:pk>/delete/', views.OsobaDelete.as_view(), name='osoba-delete'),

    # Zarządzanie adresami osób
    path('osoba/adres/create/', views.adres_osoba_create, name='adres-osoba-create'),
    path('osoba/adres/update/get', views.adres_osoba_update, name='adres-osoba-update-get'),
    path('osoba/adres/<int:pk>/update/save', views.adres_osoba_update_saving, name='adres-osoba-update-save'),
    path('osoba/adres/<int:pk>/delete', views.adres_osoba_delete, name='adres-osoba-delete'),

    # Zarządzanie zdarzeniami
    path('zdarzenie/', views.ZdarzenieList.as_view(), name='zdarzenie-list'),
    path('kontrahent/<int:pk>/zdarzenia/', views.ZdarzeniaDlaKontrahenta.as_view(), name='kontrahent-zdarzenia'),
    path('kontrahent/<int:pk>/zdarzenie/create/', views.ZdarzenieCreate.as_view(), name='zdarzenie-create'),
    path('zdarzenie/create/', views.ZdarzenieCreate.as_view(), name='zdarzenie-create'),
    path('zdarzenie/<int:pk>/', views.ZdarzenieDetail.as_view(), name='zdarzenie-detail'),
    path('zdarzenie/<int:pk>/update/', views.ZdarzenieUpdate.as_view(), name='zdarzenie-update'),
    path('zdarzenie/<int:pk>/delete/', views.ZdarzenieDelete.as_view(), name='zdarzenie-delete'),

    # produkty
    path('produkty/', views.ProduktyList.as_view(), name='produkty-list'),

    # oferty
    path('kontrahent/<int:pk>/oferty/', views.OfertyDlaKontrahenta.as_view(), name='kontrahent-oferty'),
    path('kontrahent/<int:pk>/oferty/create', views.OfertaCreate.as_view(), name='oferta-create'),
    path('kontrahent/<int:pk>/oferty/<int:pk_oferty>/update/', views.OfertaUpdate.as_view(),
        name='oferta-update'),
    path('kontrahent/<int:pk>/oferty/<int:pk_oferty>/', views.OfertaDetail.as_view(), name='oferta-detail'),
    path('kontrahent/<int:pk>/oferty/delete', views.OfertaDelete.as_view(), name='oferta-delete'),

    # umowy
    path('kontrahent/<int:pk>/umowy/', views.UmowyDlaKontrahenta.as_view(), name='kontrahent-umowy'),
    path('kontrahent/<int:pk>/umowy/create', views.UmowaCreate.as_view(), name='umowa-create'),
    path('kontrahent/<int:pk>/umowy/<int:pk_umowy>/update/', views.UmowaUpdate.as_view(), name='umowa-update'),
    # np. kontrahent/7/umowy/14
    path('kontrahent/<int:pk>/umowy/<int:pk_umowy>/', views.UmowaDetail.as_view(), name='umowa-detail'),
    path('kontrahent/<int:pk>/umowy/delete', views.UmowaDelete.as_view(), name='umowa-delete'),
    path('kontrahent/<int:pk>/umowy/valid', views.umowa_valid, name='umowa-valid'),

    # widoki dla opiekuna
    path('moi-klienci/', views.OpiekunKlienci.as_view(), name='opiekun-klienci-list'),
    path('moje-umowy/', views.OpiekunUmowy.as_view(), name='opiekun-umowy-list'),
    path('moje-zdarzenia/', views.OpiekunZdarzenia.as_view(), name='opiekun-zdarzenia-list'),
    path('moje-oferty/', views.OpiekunOferty.as_view(), name='opiekun-oferty-list'),

    # Edycja wybranej płatności np.
    # platnosc/47/update
    path('platnosc/<int:pk>/update', views.PlatnoscUpdate.as_view(), name='platnosc-update')
]
