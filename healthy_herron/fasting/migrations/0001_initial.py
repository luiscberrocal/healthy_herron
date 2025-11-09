# Generated manually for Fast model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_modified', to=settings.AUTH_USER_MODEL, verbose_name='Modified by')),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, help_text='When the fast began', verbose_name='Start Time')),
                ('end_time', models.DateTimeField(blank=True, help_text='When the fast ended', null=True, verbose_name='End Time')),
                ('emotional_status', models.CharField(blank=True, choices=[('energized', 'Energized'), ('satisfied', 'Satisfied'), ('challenging', 'Challenging'), ('difficult', 'Difficult')], help_text="User's emotional state when ending fast", max_length=20, null=True, verbose_name='Emotional Status')),
                ('comments', models.TextField(blank=True, help_text='User\'s reflection on the fast (max 128 characters)', max_length=128, verbose_name='Comments')),
                ('user', models.ForeignKey(db_index=True, help_text='Owner of the fast record', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Fast',
                'verbose_name_plural': 'Fasts',
                'ordering': ['-start_time'],
                'permissions': [('view_own_fast', 'Can view own fasting records'), ('change_own_fast', 'Can change own fasting records'), ('delete_own_fast', 'Can delete own fasting records')],
            },
        ),
        migrations.AddIndex(
            model_name='fast',
            index=models.Index(fields=['user', '-start_time'], name='fasting_fas_user_id_2ed6b4_idx'),
        ),
        migrations.AddIndex(
            model_name='fast',
            index=models.Index(fields=['user', 'end_time'], name='fasting_fas_user_id_31a1b5_idx'),
        ),
    ]