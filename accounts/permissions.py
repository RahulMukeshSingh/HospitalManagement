from rest_framework import permissions

class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.roles.name == 'admin':
                return True
        return False

class IsRegistration(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.roles.name == 'registrar':
                return True
        return False

class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.roles.name == 'doctor':
                return True
        return False        

class IsRegistrationOrDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.roles.name == 'registrar' or request.user.roles.name == 'doctor':
                return True
        return False     

class IsDispensary(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.roles.name == 'dispensary':
                return True
        return False                    
