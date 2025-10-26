# Generated manually for timezone field addition

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='timezone',
            field=models.CharField(
                default='UTC',
                help_text="User's timezone for accurate fasting time tracking",
                max_length=50,
                verbose_name='Timezone'
            ),
        ),
    ]