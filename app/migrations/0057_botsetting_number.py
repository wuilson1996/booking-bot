# Generated by Django 4.2.20 on 2025-04-08 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0056_rename_bot_automatization_botrange_bot_setting'),
    ]

    operations = [
        migrations.AddField(
            model_name='botsetting',
            name='number',
            field=models.IntegerField(default=1),
        ),
    ]
