from django.db import models
from accounts.models import Account, Department, Hospital
from registration.models import Appointment
from django.utils.translation import gettext_lazy as _
# Create your models here.
class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(Account, on_delete = models.CASCADE)
    not_available = models.JSONField()
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return self.not_available

class Diagnosis(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete = models.CASCADE)
    diagnosis = models.TextField(verbose_name = _('Diagnosis'))
    symptoms = models.TextField(verbose_name = _('Symptoms'))
    medicine = models.JSONField() #{id, qty} -> {id, name, qty, price}
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return self.not_available


         