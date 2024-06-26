# Generated by Django 5.0 on 2024-02-11 16:15

import django.db.models.deletion
import shortuuid.django_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cid', shortuuid.django_fields.ShortUUIDField(alphabet='abc12345', length=22, max_length=50, prefix='zoro', unique=True)),
                ('title', models.CharField(default='Merch', max_length=100)),
                ('image', models.ImageField(blank=True, default='category.jpg', null=True, upload_to='category')),
                ('is_blocked', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sizename', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='UserDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(blank=True, max_length=200, null=True)),
                ('bio', models.CharField(blank=True, max_length=200, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('code', models.CharField(blank=True, max_length=12, null=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pid', shortuuid.django_fields.ShortUUIDField(alphabet='abcdefghi1234567', length=10, max_length=20, prefix='', unique=True)),
                ('title', models.CharField(default='hoodie', max_length=100)),
                ('image', models.ImageField(blank=True, default='product.jpg', null=True, upload_to='user_images')),
                ('descriptions', models.TextField(blank=True, default='this is a good hoodie', null=True)),
                ('price', models.DecimalField(decimal_places=2, default='749.99', max_digits=10)),
                ('old_price', models.DecimalField(decimal_places=2, default='799.43', max_digits=10)),
                ('specifications', models.TextField(blank=True, default='This hoodie has a roundneck', null=True)),
                ('status', models.BooleanField(default=True)),
                ('in_stock', models.BooleanField(default=True)),
                ('featured', models.BooleanField(default=True)),
                ('sku', shortuuid.django_fields.ShortUUIDField(alphabet='abcdefghi1234567', length=4, max_length=10, prefix='sku', unique=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(blank=True, null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.category')),
            ],
            options={
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Images', models.ImageField(default='product.jpg', upload_to='products-images')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='p_images', to='app.product')),
            ],
            options={
                'verbose_name_plural': 'Product images',
            },
        ),
        migrations.CreateModel(
            name='ProductVarients',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vid', shortuuid.django_fields.ShortUUIDField(alphabet='abcdefghi1234567', length=10, max_length=20, prefix='', unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Variant', to='app.product')),
                ('size', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.size')),
            ],
            options={
                'verbose_name_plural': 'Product variants',
            },
        ),
        migrations.CreateModel(
            name='SizeStockCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_count', models.IntegerField(default=0)),
                ('varient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.productvarients')),
            ],
        ),
    ]
