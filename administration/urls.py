from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
app_name = 'administration'
router = DefaultRouter()
router.register('api/departments', views.DepartmentView, basename='api_department')
router.register('api/roles', views.RolesView, basename='api_roles')
router.register('api/staff', views.StaffView, basename='api_staff')


urlpatterns = [
    # path('departments/',views.department_request, name = "department"), 
    # path('roles/',views.roles_request, name = "roles"),
    # path('staff/',views.staff_request, name = 'staff'),
]

urlpatterns += router.urls