# Generated by Django 2.0.5 on 2018-05-24 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('yellowant_api', '0003_awsec2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='awsec2',
            name='user_integration',
        ),
        migrations.AlterField(
            model_name='awsec2',
            name='id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='yellowant_api.UserIntegration'),
        ),
    ]