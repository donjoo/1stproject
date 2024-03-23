# Generated by Django 5.0 on 2024-03-17 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_stock'),
        ('orders', '0005_alter_orderproduct_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='variation',
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='variations',
            field=models.ManyToManyField(blank=True, to='app.variants'),
        ),
    ]
