# Generated by Django 3.2.13 on 2022-08-05 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_otp'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OTP',
        ),
    ]