# Generated by Django 3.1.2 on 2020-10-30 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_page', '0003_auto_20190516_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='testpage',
            name='publish_to_live_release',
            field=models.BooleanField(default=False),
        ),
    ]