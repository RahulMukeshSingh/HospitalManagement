from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Hospital
from registration.models import Appointment

# Create your models here.
class Medicine(models.Model):
    name =  models.CharField(verbose_name = _('Medicine Name'), max_length = 255)
    used_for = models.TextField(verbose_name = _('Used For'))
    quantity = models.PositiveIntegerField(verbose_name = _('Quantity'))
    price = models.DecimalField(verbose_name = _('Price'), max_digits = 10, decimal_places = 2)
    discount_percent = models.DecimalField(verbose_name = _('Discount (%)'), max_digits = 5, decimal_places = 2)
    date_added = models.DateTimeField(verbose_name = _('Date Added'), auto_now_add = True)
    last_modified = models.DateTimeField(verbose_name = _('Last Modified'), auto_now = True) 
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return self.name

class Bill(models.Model):
    bill_date =  models.DateTimeField(verbose_name = _('Bill Date'), auto_now_add = True)
    appointment = models.ForeignKey(Appointment, on_delete = models.CASCADE)
    details = models.JSONField() #{Doctor Fees, [medicine, qty, price]}
    total_price = models.DecimalField(verbose_name = _('Total Price'), max_digits = 15, decimal_places = 2)
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return str(self.total_price)


payment_choices = (
    ('credit_card', 'credit card'),
    ('debit_card', 'debit card'),
    ('upi', 'upi'),
    ('net_banking', 'net banking'),
    ('cash', 'cash')
)

class Transaction(models.Model):
    transaction_date = models.DateTimeField(verbose_name = _('Transaction Date'), auto_now_add = True)
    bill = models.ForeignKey(Bill, on_delete = models.CASCADE)
    amount = models.DecimalField(verbose_name = _('Amount'), max_digits = 15, decimal_places = 2)
    payment_mode = models.CharField(max_length = 11, choices = payment_choices)
    hospital = models.ForeignKey(Hospital, on_delete = models.CASCADE, blank = True, null = True)

    def __str__(self):
        return str(self.amount)       
