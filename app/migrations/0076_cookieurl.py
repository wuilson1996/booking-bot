# Generated by Django 3.2 on 2025-06-24 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0075_price_active_sync'),
    ]

    operations = [
        migrations.CreateModel(
            name='CookieUrl',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('label', models.TextField()),
            ],
        ),
    ]
