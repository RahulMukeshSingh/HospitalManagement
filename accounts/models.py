from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

#--------------------------------------------------------------------------------------
class Hospital(models.Model):
    name = models.CharField(verbose_name = _('Hospital Name'), max_length=100)
    date_created = models.DateTimeField(verbose_name = _('Date Created'), auto_now_add = True)
    date_modified = models.DateTimeField(verbose_name = _('Date Modified'), auto_now = True)

    def __str__(self):
        return self.name  
#--------------------------------------------------------------------------------------
class Roles(models.Model):
    name = models.CharField(verbose_name = _('Role'), max_length=100)
    date_created = models.DateTimeField(verbose_name = _('Date Created'), auto_now_add = True)
    date_modified = models.DateTimeField(verbose_name = _('Date Modified'), auto_now = True) 
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE)

    def __str__(self):
        return self.name 
#--------------------------------------------------------------------------------------
class Department(models.Model) :
    name = models.CharField(verbose_name = _('Department Name'), max_length = 50)
    fees = models.DecimalField(verbose_name = _('Total Price'), max_digits = 15, decimal_places = 2, default = 500)
    date_created = models.DateTimeField(verbose_name = _('Date Created'), auto_now_add = True)
    date_modified = models.DateTimeField(verbose_name = _('Date Modified'), auto_now = True) 
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE)

    def __str__(self):
        return self.name
#--------------------------------------------------------------------------------------
class AccountsManager(BaseUserManager):
    def create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError(_("User must have an Email Address."))
        user = self.model(email = self.normalize_email(email), name = name, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_superuser(self, email, name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) 
        return self.create_user(email, name, password, **extra_fields)
#--------------------------------------------------------------------------------------
class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name = _('Email'), max_length = 100, unique = True)
    mobile = models.CharField(verbose_name = _('Mobile No'), max_length = 10, unique = True, blank = True, null = True)
    name = models.CharField(verbose_name = _('Full Name'), max_length = 255)
    date_joined = models.DateTimeField(verbose_name = _('Joining Date'), auto_now_add = True)
    last_login = models.DateTimeField(verbose_name = _('Last Login'), auto_now = True)
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)
    is_superuser = models.BooleanField(default = False)
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)
    roles = models.ForeignKey(Roles, on_delete = models.SET_NULL, blank = True, null = True)
    department = models.ForeignKey(Department, on_delete = models.SET_NULL, blank = True, null = True)

    objects = AccountsManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name + f"({self.pk})"

#--------------------------------------------------------------------------------------
class OTP(models.Model):
    account = models.OneToOneField(Account, on_delete = models.CASCADE, primary_key = True)
    otp = models.CharField(max_length = 6)
    generated_time = models.DateTimeField(auto_now = True)