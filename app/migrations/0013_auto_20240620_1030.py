# Generated by Django 3.2 on 2024-06-20 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_availablebooking_currenct'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='availablebooking',
            name='currenct',
        ),
        migrations.AddField(
            model_name='processactive',
            name='currenct',
            field=models.BooleanField(default=False),
        ),
    ]
