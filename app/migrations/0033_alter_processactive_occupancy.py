# Generated by Django 3.2 on 2024-11-25 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0032_alter_temporadabyday_bg_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processactive',
            name='occupancy',
            field=models.IntegerField(choices=[(1, 'City'), (2, 'Name')], default=1),
        ),
    ]