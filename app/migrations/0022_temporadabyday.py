# Generated by Django 3.2 on 2024-08-10 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_auto_20240809_1250'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemporadaByDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_from', models.CharField(max_length=30)),
                ('bg_color', models.TextField(choices=[('bg-success', 'bg-success'), ('bg-warning', 'bg-warning'), ('bg-info', 'bg-info'), ('bg-primary', 'bg-primary'), ('bg-secondary', 'bg-secondary'), ('bg-dark', 'bg-dark')], default='bg-success')),
                ('text_color', models.TextField(choices=[('text-success', 'text-success'), ('text-warning', 'text-warning'), ('text-info', 'text-info'), ('text-secondary', 'text-secondary'), ('text-dark', 'text-dark'), ('text-white', 'text-white'), ('text-black', 'text-black'), ('text-primary', 'text-primary')], default='text-success')),
                ('numer', models.CharField(max_length=3)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('created', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]