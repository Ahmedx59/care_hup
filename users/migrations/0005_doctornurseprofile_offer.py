# Generated by Django 5.1.3 on 2025-03-16 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_doctornurseprofile_certificates'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctornurseprofile',
            name='offer',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
