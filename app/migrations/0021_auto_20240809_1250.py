# Generated by Django 3.2 on 2024-08-09 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_eventbyday_messagebyday_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventbyday',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='eventbyday',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='messagebyday',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='messagebyday',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='price',
            name='created',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='price',
            name='updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='eventbyday',
            name='occupancy',
            field=models.IntegerField(choices=[(2, '2 Personas'), (3, '3 Personas'), (5, '5 Personas')], default=2),
        ),
        migrations.AlterField(
            model_name='messagebyday',
            name='occupancy',
            field=models.IntegerField(choices=[(2, '2 Personas'), (3, '3 Personas'), (5, '5 Personas')], default=2),
        ),
        migrations.AlterField(
            model_name='price',
            name='occupancy',
            field=models.IntegerField(choices=[(2, '2 Personas'), (3, '3 Personas'), (5, '5 Personas')], default=2),
        ),
    ]