# Generated by Django 4.0.4 on 2022-09-05 17:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('suite', '0006_artefacto_ultima_modificacion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='artefacto',
            name='ultima_modificacion',
        ),
    ]
