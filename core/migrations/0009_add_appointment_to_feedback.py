# Generated migration to add appointment_id to feedback table

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_notification_options_notification_appointment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='appointment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedbacks', to='core.appointment'),
        ),
    ]