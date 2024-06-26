# Generated by Django 3.2.25 on 2024-04-19 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pro_app', '0010_auto_20240418_0631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='description',
            field=models.TextField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='brand',
            name='name',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='categoryofproducts',
            name='title',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='inventorydepartmentmodel',
            name='quantity',
            field=models.IntegerField(default=True),
        ),
        migrations.AlterField(
            model_name='prod_col',
            name='color',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='productdetails',
            name='description',
            field=models.TextField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='productdetails',
            name='name',
            field=models.CharField(db_index=True, default='', help_text='Name of product', max_length=255),
        ),
        migrations.AlterField(
            model_name='productdetails',
            name='review',
            field=models.TextField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='productdetails',
            name='sku_number',
            field=models.CharField(db_index=True, default=False, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='storedepotmodel',
            name='Country_code',
            field=models.CharField(default='', max_length=3),
        ),
        migrations.AlterField(
            model_name='storedepotmodel',
            name='address',
            field=models.CharField(default='', help_text='enter your address here', max_length=255),
        ),
        migrations.AlterField(
            model_name='storedepotmodel',
            name='contacts',
            field=models.IntegerField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='storedepotmodel',
            name='store_email',
            field=models.EmailField(db_index=True, default='', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='storedepotmodel',
            name='store_name',
            field=models.CharField(default='', max_length=255),
        ),
    ]
