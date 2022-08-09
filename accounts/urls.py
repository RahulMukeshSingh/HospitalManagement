from django.urls import path
from . import views
#from rest_framework.authtoken import views
from rest_framework_simplejwt.views import TokenVerifyView , TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    #path('api/login/', views.obtain_auth_token, name = 'api_login'),
    #path('api/login/', TokenObtainPairView.as_view(), name = 'api_login'),
    path('api/login/', views.LoginRegisterView.as_view({'post' : 'login'}), name = 'api_login'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name = 'api_login_refresh'),
    path('api/register/', views.LoginRegisterView.as_view({'post' : 'create'}), name = 'api_register'),
    path('api/otp/', views.LoginRegisterView.as_view({'post' : 'mail_otp'}), name = 'api_otp'),    
    path('api/reset/password/', views.LoginRegisterView.as_view({'post' : 'forget_password'}), name = 'api_forget_password'),    
    path('api/logout/', views.LogoutView.as_view({'post' : 'logout'}), name = 'api_logout'),
    path('api/logout/all/', views.LogoutView.as_view({'post' : 'logout_all_devices'}), name = 'api_logout_all'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]