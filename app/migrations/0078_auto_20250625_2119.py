# Generated by Django 3.2 on 2025-06-26 02:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0077_auto_20250625_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='cookieurl',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2025, 6, 25, 0, 0)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='messagename',
            name='bg_color',
            field=models.TextField(choices=[('#90EE90', 'verde'), ('#FF0000', 'rojo'), ('#ff7d60', 'naranja'), ('#6cb7fc', 'azul-claro'), ('#317ec6', 'azul-oscuro')], default='rojo'),
        ),
    ]
