# Generated by Django 3.2.13 on 2022-08-05 11:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_appointment_diagnosed'),
        ('dispensary', '0006_medicine_discount_percent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='appointment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration.appointment'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='bill',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dispensary.bill'),
        ),
    ]
