from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'dispensary'

router = DefaultRouter()
router.register('api/medicine', views.MedicineView, basename='api_medicine')
router.register('api/bill', views.BillView, basename='api_bill')
router.register('api/transaction', views.TransactionView, basename='api_transaction')

urlpatterns = [
]

urlpatterns += router.urls