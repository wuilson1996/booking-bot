# Generated by Django 3.2 on 2024-11-25 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0034_auto_20241125_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalsearch',
            name='type_search',
            field=models.IntegerField(choices=[(1, 'City'), (2, 'Name')], default=1),
        ),
    ]
