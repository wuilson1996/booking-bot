# Generated by Django 4.2.20 on 2025-04-08 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0052_botsetting_taskexecute_remove_processactive_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='botrange',
            name='number',
            field=models.IntegerField(default=1),
        ),
    ]
