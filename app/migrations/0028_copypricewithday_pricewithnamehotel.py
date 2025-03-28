# Generated by Django 3.2 on 2024-11-01 03:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_auto_20240826_1518'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceWithNameHotel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.CharField(max_length=20)),
                ('title', models.CharField(max_length=512)),
                ('link', models.CharField(max_length=3000)),
                ('address', models.CharField(max_length=512)),
                ('distance', models.CharField(max_length=512)),
                ('description', models.CharField(max_length=1024)),
                ('img', models.CharField(max_length=3000)),
                ('updated', models.DateTimeField()),
                ('created', models.DateTimeField()),
                ('date_from', models.CharField(max_length=30)),
                ('date_to', models.CharField(max_length=30)),
                ('price', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='CopyPriceWithDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.CharField(max_length=30)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('avail_booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.availablebooking')),
            ],
        ),
    ]
