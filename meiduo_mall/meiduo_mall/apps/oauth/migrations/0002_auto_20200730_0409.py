# Generated by Django 2.2.5 on 2020-07-30 04:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='oauthqquser',
            old_name='uodate_time',
            new_name='update_time',
        ),
    ]
