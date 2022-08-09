from django.contrib import admin
from accounts.models import Account
from django.contrib.auth.admin import UserAdmin
# Register your models here.
class AccountsAdmin(UserAdmin):
    list_display = ['email', 'name', 'date_joined', 'last_login', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'name']
    readonly_fields = ['last_login' ,'date_joined']
    filter_horizontal = []
    list_filter = []
    #Admin Edit Page
    fieldsets = [
        ('Edit User Details', 
        {'fields': 
        ('email', 'name', 'date_joined', 'last_login', 'is_active', 'is_staff', 'is_superuser', 'hospital', 'groups')
        }
        ),
    ]
    #Admin Add Page
    add_fieldsets = [
        ('Add User Details', 
        {'fields': 
        ('email', 'name', 'password1', 'password2', 'is_staff', 'is_superuser', 'hospital', 'groups')
        }
        ),
    ]
    ordering = ['email']

admin.site.register(Account, AccountsAdmin)