# Generated by Django 5.1.3 on 2025-04-15 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_doctornurseprofile_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctornurseprofile',
            name='services',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]
