# Generated by Django 2.0.5 on 2018-06-23 12:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0004_auto_20180622_2013'),
    ]

    operations = [
        migrations.RenameField(
            model_name='channel',
            old_name='node1',
            new_name='node1_pub',
        ),
        migrations.RenameField(
            model_name='channel',
            old_name='node2',
            new_name='node2_pub',
        ),
    ]