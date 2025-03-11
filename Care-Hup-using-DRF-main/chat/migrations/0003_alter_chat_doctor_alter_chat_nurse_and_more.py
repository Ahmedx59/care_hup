# Generated by Django 5.1.3 on 2025-02-18 15:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_chat_nurse_message_is_read_alter_chat_doctor'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_chats', to='users.doctornurseprofile'),
        ),
        migrations.AlterField(
            model_name='chat',
            name='nurse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='nurse_chats', to='users.doctornurseprofile'),
        ),
        migrations.AlterField(
            model_name='chat',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_chats', to='users.patientprofile'),
        ),
    ]
