# Generated by Django 3.2.13 on 2022-07-12 08:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_account_mobile'),
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctoravailability',
            name='hospital',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.hospital'),
        ),
        migrations.AddField(
            model_name='token',
            name='hospital',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.hospital'),
        ),
    ]