# Generated by Django 5.0 on 2024-03-25 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_order_category_offer_order_product_offer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='category_offer',
        ),
        migrations.RemoveField(
            model_name='order',
            name='product_offer',
        ),
        migrations.AddField(
            model_name='order',
            name='offer_price',
            field=models.FloatField(blank=True, default=0),
        ),
    ]