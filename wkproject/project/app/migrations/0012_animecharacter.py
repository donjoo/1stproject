# Generated by Django 5.0 on 2024-02-23 06:48

import django.db.models.deletion
import shortuuid.django_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_delete_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnimeCharacter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lid', shortuuid.django_fields.ShortUUIDField(alphabet='abc12345', length=22, max_length=50, prefix='anichar', unique=True)),
                ('name', models.CharField(default='tokyo', max_length=100)),
                ('image', models.ImageField(blank=True, default='char.jpg', null=True, upload_to='character')),
                ('is_blocked', models.BooleanField(default=False)),
                ('animename', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chracter', to='app.categoryanime')),
            ],
            options={
                'verbose_name_plural': 'AnimeCharacter',
            },
        ),
    ]
