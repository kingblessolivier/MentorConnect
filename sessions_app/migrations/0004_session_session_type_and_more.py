# Generated manually - Session model extensions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessions_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='session_type',
            field=models.CharField(choices=[('online', 'Online'), ('physical', 'Physical / In-Person')], default='online', max_length=20, verbose_name='Session Type'),
        ),
        migrations.AddField(
            model_name='session',
            name='location_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Location Name'),
        ),
        migrations.AddField(
            model_name='session',
            name='address',
            field=models.TextField(blank=True, verbose_name='Address'),
        ),
        migrations.AddField(
            model_name='session',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Latitude'),
        ),
        migrations.AddField(
            model_name='session',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Longitude'),
        ),
        migrations.AddField(
            model_name='session',
            name='student_attended',
            field=models.BooleanField(blank=True, null=True, verbose_name='Student Attended'),
        ),
        migrations.AddField(
            model_name='session',
            name='mentor_attended',
            field=models.BooleanField(blank=True, null=True, verbose_name='Mentor Attended'),
        ),
    ]
