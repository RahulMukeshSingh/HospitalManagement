from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
app_name = 'doctor'
router = DefaultRouter()
router.register('api/appointment', views.DoctorAppointmentView, basename='api_doctor_appointment')
router.register('api/token', views.DoctorTokenView, basename='api_doctor_token')
router.register('api/diagnosis', views.DiagnosisView, basename='api_diagnosis')



urlpatterns = [
    path('api/availability/', views.DoctorAvailabilityView.as_view({'get':'list','post':'create'}), name = "api_availability"),
    path('api/availability/doctors/', views.DoctorAvailabilityView.as_view({'get':'get_doctors_availability'}), name = "api_doctors_availability"),
    path('api/availability/holiday/<str:date_delete>/', views.DoctorAvailabilityView.as_view({'delete':'destroy'}), name = "api_availability"),
]

urlpatterns += router.urls