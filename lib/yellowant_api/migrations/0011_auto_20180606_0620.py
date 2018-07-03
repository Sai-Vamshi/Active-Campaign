# Generated by Django 2.0.6 on 2018-06-06 06:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('yellowant_api', '0010_auto_20180529_1258'),
    ]

    operations = [
        migrations.CreateModel(
            name='active_campaign',
            fields=[
                ('id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='yellowant_api.UserIntegration')),
                ('API_Access_URL', models.CharField(max_length=100)),
                ('API_Access_key', models.CharField(max_length=100)),
                ('AWS_update_login_flag', models.BooleanField(default=False, max_length=2)),
            ],
        ),
        migrations.RemoveField(
            model_name='awss3',
            name='id',
        ),
        migrations.DeleteModel(
            name='awss3',
        ),
    ]