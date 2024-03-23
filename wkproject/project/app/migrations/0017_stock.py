# Generated by Django 5.0 on 2024-03-04 06:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_alter_productvariants_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock', models.IntegerField(default=0)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.variants')),
            ],
        ),
    ]
