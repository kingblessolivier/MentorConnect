# Generated manually for applications app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GuestApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Full Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('school', models.CharField(max_length=200, verbose_name='School/Institution')),
                ('interests', models.TextField(verbose_name='Interests')),
                ('message', models.TextField(verbose_name='Message')),
                ('cv', models.FileField(blank=True, null=True, upload_to='applications/cvs/', verbose_name='CV/Resume')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('mentor_feedback', models.TextField(blank=True, verbose_name='Mentor Feedback')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejected_at', models.DateTimeField(blank=True, null=True)),
                ('mentor', models.ForeignKey(limit_choices_to={'role': 'mentor'}, on_delete=django.db.models.deletion.CASCADE, related_name='guest_applications', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_guest_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Guest Application',
                'verbose_name_plural': 'Guest Applications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InvitationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='invitation_token', to='applications.guestapplication')),
            ],
            options={
                'verbose_name': 'Invitation Token',
                'verbose_name_plural': 'Invitation Tokens',
                'ordering': ['-created_at'],
            },
        ),
    ]
