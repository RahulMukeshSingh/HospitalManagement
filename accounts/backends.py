from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from accounts.models import Account


class HospitalAuthenticationBackend(ModelBackend):

    def authenticate(self, request, username = None, password = None, **kwargs):
        try:
            account = Account.objects.get(Q(email = username) | Q(mobile = username))
            if self.user_can_authenticate(account) and account.check_password(password):
                return account     
        except Account.DoesNotExist:
            return None
        return None    
