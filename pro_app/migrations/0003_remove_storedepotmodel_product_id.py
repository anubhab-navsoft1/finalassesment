# Generated by Django 3.2.25 on 2024-04-15 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pro_app', '0002_auto_20240415_0645'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storedepotmodel',
            name='product_id',
        ),
    ]
