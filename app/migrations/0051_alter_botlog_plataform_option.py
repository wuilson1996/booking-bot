# Generated by Django 4.2.20 on 2025-04-08 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0050_tasklock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botlog',
            name='plataform_option',
            field=models.TextField(choices=[('suitesferia', 'suitesferia'), ('roomprice', 'roomprice'), ('booking', 'booking'), ('history', 'history')], default='booking'),
        ),
    ]
