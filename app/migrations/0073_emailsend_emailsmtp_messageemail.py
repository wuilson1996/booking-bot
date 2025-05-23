# Generated by Django 3.2 on 2025-05-19 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0072_alter_screenshotlog_descripcion'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='EmailSMTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=100)),
                ('host', models.CharField(max_length=100)),
                ('port', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='MessageEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asunto', models.CharField(max_length=256)),
                ('message', models.TextField()),
                ('type_message', models.TextField(choices=[('CheckEmail', 'CheckEmail'), ('SendFile', 'SendFile'), ('Notify', 'Notify')], default='Notify')),
                ('email', models.ManyToManyField(to='app.EmailSend')),
            ],
        ),
    ]
