# Generated by Django 3.2 on 2024-08-06 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_availsuitesferia_cantavailsuitesferia'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='occupancy',
        ),
        migrations.AddField(
            model_name='availablebooking',
            name='occupancy',
            field=models.IntegerField(default=4),
        ),
        migrations.AlterField(
            model_name='availsuitesferia',
            name='date_avail',
            field=models.CharField(max_length=50),
        ),
    ]
