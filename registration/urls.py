from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'registration'

router = DefaultRouter()
router.register('api/patient', views.PatientView, basename='api_patient')
router.register('api/appointment', views.AppointmentView, basename='api_appointment')
router.register('api/token', views.TokenView, basename='api_token')

urlpatterns = [
    # path('patient/',views.patient_request, name = "patient"),
    # path('appointment/',views.appointment_request, name = "appointment"),
    # path('token/',views.token_request, name = "token"),    
    #path('api/appointment/', views.AppointmentView.as_view() ,name = "api_appointment"),
]

urlpatterns += router.urls