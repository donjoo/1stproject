# Generated by Django 5.0 on 2024-03-03 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_product_anime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariants',
            name='size',
            field=models.CharField(choices=[('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')], max_length=3),
        ),
    ]
