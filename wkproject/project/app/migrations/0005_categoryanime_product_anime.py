# Generated by Django 5.0 on 2024-02-19 15:59

import django.db.models.deletion
import shortuuid.django_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_userdetails_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryAnime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aid', shortuuid.django_fields.ShortUUIDField(alphabet='abc12345', length=22, max_length=50, prefix='anime', unique=True)),
                ('title', models.CharField(default='anime', max_length=100)),
                ('image', models.ImageField(blank=True, default='anime.jpg', null=True, upload_to='anime')),
                ('is_blocked', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Anime',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='anime',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.categoryanime'),
        ),
    ]
