# Generated by Django 3.2 on 2024-11-26 23:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0035_generalsearch_type_search'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalsearch',
            name='proces_active',
            field=models.ManyToManyField(blank=True, null=True, to='app.ProcessActive'),
        ),
    ]