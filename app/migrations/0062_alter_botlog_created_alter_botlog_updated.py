# Generated by Django 4.2.20 on 2025-04-12 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0061_alter_complement_created_alter_complement_updated_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botlog',
            name='created',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='botlog',
            name='updated',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
