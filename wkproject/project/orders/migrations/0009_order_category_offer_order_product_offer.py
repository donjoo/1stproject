# Generated by Django 5.0 on 2024-03-25 15:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_categoryoffer_productoffer_referraloffer'),
        ('orders', '0008_order_coupon_order_shipping'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='category_offer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.categoryoffer'),
        ),
        migrations.AddField(
            model_name='order',
            name='product_offer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.productoffer'),
        ),
    ]