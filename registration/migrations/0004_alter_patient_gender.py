# Generated by Django 3.2.13 on 2022-07-13 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_rename_last_login_patient_last_accessed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='gender',
            field=models.CharField(choices=[('m', 'male'), ('f', 'female'), ('o', 'others')], max_length=1),
        ),
    ]
