# Generated by Django 2.2.6 on 2019-10-22 09:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailsnapshotpublisher', '0004_auto_20190423_1417'),
    ]

    operations = [
        migrations.AddField(
            model_name='wsspcontentrelease',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
