from django.urls import path
from . import views

app_name = 'platnosci'
urlpatterns = [
    path('kalendarz/', views.CalendarView.as_view(), name='kalendarz'),
    path('lista/', views.PaymentListView.as_view(), name='lista'),
    path('get_payment_data/<int:pk>', views.get_payment_data, name='payment-update'),
    path('save_payment_data/<int:pk>', views.save_payment_data, name='payment-update-save'),
]