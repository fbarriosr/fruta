# Generated by Django 3.1.7 on 2025-01-28 18:22

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_auto_20250128_1459'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeZoneChoices',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='trip',
            name='arrival_timezone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='arrival_trips', to='dashboard.timezonechoices'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='departure_timezone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='departure_trips', to='dashboard.timezonechoices'),
        ),
    ]
