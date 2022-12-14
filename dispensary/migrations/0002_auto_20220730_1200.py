# Generated by Django 3.2.13 on 2022-07-30 12:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dispensary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='bill_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Transaction Date'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Transaction Date'),
        ),
    ]
