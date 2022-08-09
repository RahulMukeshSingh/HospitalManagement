from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Account, Department, Hospital
# Create your models here.

gender_choices = (
    ('m', 'male'),
    ('f', 'female'),
    ('o', 'others'),
)

class Patient(models.Model):
    email = models.EmailField(verbose_name = _('Email'), max_length = 100)
    mobile = models.CharField(verbose_name=_('Mobile No'), max_length = 10)
    name = models.CharField(verbose_name = _('Full Name'), max_length = 255)
    dob = models.DateField(verbose_name = _('Date of Birth'))
    gender = models.CharField(max_length = 1, choices = gender_choices)
    register_date = models.DateTimeField(verbose_name = _('Register Date'), auto_now_add = True)
    last_accessed = models.DateTimeField(verbose_name = _('Last Login'), auto_now = True)
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)


    def __str__(self):
        return self.name + f"({self.pk})"


class Appointment(models.Model):
    appointment_date = models.DateField(verbose_name = _('Appointment Date'))
    present = models.BooleanField(verbose_name = _('Present'), default = False)
    diagnosed = models.BooleanField(verbose_name = _('Diagnosed'), default = False) 
    patient = models.ForeignKey(Patient, on_delete = models.CASCADE)
    doctor = models.ForeignKey(Account, on_delete = models.SET_NULL, null = True)
    department = models.ForeignKey(Department, on_delete = models.SET_NULL, null = True)
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)


    def __str__(self):
        return str(self.pk)

# class Token(models.Model):
#     appointment = models.ForeignKey(Appointment, on_delete = models.CASCADE, blank = True, null = True)
#     hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

#     def __str__(self):
#         return self.pk
