# Generated by Django 2.0.5 on 2018-06-23 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0005_auto_20180623_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='node1_pub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='node1_pub', to='nodes.Node'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='node2_pub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='node2_pub', to='nodes.Node'),
        ),
    ]