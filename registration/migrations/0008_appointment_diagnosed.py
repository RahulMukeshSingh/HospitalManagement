# Generated by Django 3.2.13 on 2022-07-28 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0007_auto_20220727_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='diagnosed',
            field=models.BooleanField(default=False, verbose_name='Diagnosed'),
        ),
    ]
