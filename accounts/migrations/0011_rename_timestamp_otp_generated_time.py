# Generated by Django 3.2.13 on 2022-08-05 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_alter_otp_account'),
    ]

    operations = [
        migrations.RenameField(
            model_name='otp',
            old_name='timestamp',
            new_name='generated_time',
        ),
    ]