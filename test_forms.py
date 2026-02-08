#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.forms import StudentRegistrationForm, MentorRegistrationForm
from accounts.models import User

print("=" * 60)
print("Testing StudentRegistrationForm")
print("=" * 60)

# Test 1: Create a StudentRegistrationForm
try:
    student_form = StudentRegistrationForm()
    print("✓ StudentRegistrationForm instantiated successfully")
    print(f"  Fields: {list(student_form.fields.keys())}")
except Exception as e:
    print(f"✗ Error instantiating StudentRegistrationForm: {e}")

# Test 2: Validate with valid data
print("\nTesting with valid student data...")
student_data = {
    'email': 'student@test.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'password1': 'TestPassword123!',
    'password2': 'TestPassword123!',
    'agree_terms': True
}
try:
    student_form = StudentRegistrationForm(data=student_data)
    if student_form.is_valid():
        print("✓ StudentRegistrationForm is valid")
        user = student_form.save()
        print(f"✓ Student user created: {user.email} (role: {user.role})")
    else:
        print(f"✗ StudentRegistrationForm validation failed:")
        for field, errors in student_form.errors.items():
            print(f"  {field}: {errors}")
except Exception as e:
    print(f"✗ Error with StudentRegistrationForm: {e}")

print("\n" + "=" * 60)
print("Testing MentorRegistrationForm")
print("=" * 60)

# Test 3: Create a MentorRegistrationForm
try:
    mentor_form = MentorRegistrationForm()
    print("✓ MentorRegistrationForm instantiated successfully")
    print(f"  Fields: {list(mentor_form.fields.keys())}")
except Exception as e:
    print(f"✗ Error instantiating MentorRegistrationForm: {e}")

# Test 4: Validate with valid data
print("\nTesting with valid mentor data...")
mentor_data = {
    'email': 'mentor@test.com',
    'first_name': 'Jane',
    'last_name': 'Smith',
    'phone': '+1234567890',
    'expertise': 'Software Engineering',
    'experience_years': 5,
    'password1': 'TestPassword123!',
    'password2': 'TestPassword123!',
    'agree_terms': True
}
try:
    mentor_form = MentorRegistrationForm(data=mentor_data)
    if mentor_form.is_valid():
        print("✓ MentorRegistrationForm is valid")
        user = mentor_form.save()
        print(f"✓ Mentor user created: {user.email} (role: {user.role})")
    else:
        print(f"✗ MentorRegistrationForm validation failed:")
        for field, errors in mentor_form.errors.items():
            print(f"  {field}: {errors}")
except Exception as e:
    print(f"✗ Error with MentorRegistrationForm: {e}")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print(f"Total users in database: {User.objects.count()}")
for user in User.objects.all():
    print(f"  - {user.email} (role: {user.role})")
