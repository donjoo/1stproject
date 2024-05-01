# Generated by Django 5.0 on 2024-04-27 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_product_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='active',
        ),
        migrations.AddField(
            model_name='animecharacter',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='category',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='categoryanime',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='categoryoffer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='categoryoffer',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='coupon',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='productoffer',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='variants',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='ReferralOffer',
        ),
    ]