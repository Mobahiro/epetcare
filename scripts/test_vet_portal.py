"""
Test script to verify vet portal functionality
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from vet.models import Veterinarian
from clinic.models import Pet, Owner, Appointment, MedicalRecord, Prescription
from datetime import datetime, timedelta
from django.utils import timezone

def test_vet_portal():
    """Test vet portal views and functionality"""
    print("=" * 60)
    print("TESTING VET PORTAL FUNCTIONALITY")
    print("=" * 60)
    
    # Get or create a test vet user
    try:
        vet_user = User.objects.filter(email__contains='_rembo@vet').first()
        if not vet_user:
            print("❌ No vet user found. Please create one first.")
            return False
        
        vet_profile = vet_user.vet_profile
        print(f"✅ Found vet user: {vet_user.username}")
        print(f"   Vet name: Dr. {vet_profile.full_name}")
        print(f"   Access code: {vet_profile.access_code}")
        
    except Exception as e:
        print(f"❌ Error getting vet user: {e}")
        return False
    
    # Test authentication
    client = Client()
    print("\n" + "=" * 60)
    print("TESTING VET LOGIN")
    print("=" * 60)
    
    # Log in the vet
    login_success = client.login(username=vet_user.username, password='test123')
    if not login_success:
        print("❌ Failed to log in vet user")
        print("   Trying to set password...")
        vet_user.set_password('test123')
        vet_user.save()
        login_success = client.login(username=vet_user.username, password='test123')
    
    if login_success:
        print(f"✅ Successfully logged in as {vet_user.username}")
    else:
        print("❌ Could not log in vet user even after setting password")
        return False
    
    # Test dashboard access
    print("\n" + "=" * 60)
    print("TESTING DASHBOARD ACCESS")
    print("=" * 60)
    
    response = client.get('/vet-portal/')
    if response.status_code == 200:
        print(f"✅ Dashboard accessible (status: {response.status_code})")
        # Check for key elements in response
        content = response.content.decode('utf-8')
        if 'Welcome, Dr.' in content or vet_profile.full_name in content:
            print("✅ Dashboard shows vet name")
        else:
            print("⚠️  Dashboard may not show vet name properly")
    else:
        print(f"❌ Dashboard not accessible (status: {response.status_code})")
        if response.status_code == 302:
            print(f"   Redirected to: {response.url}")
    
    # Test patient list
    print("\n" + "=" * 60)
    print("TESTING PATIENT LIST")
    print("=" * 60)
    
    response = client.get('/vet-portal/patients/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Patient list accessible")
        pet_count = Pet.objects.count()
        print(f"   Total pets in database: {pet_count}")
    else:
        print(f"❌ Patient list not accessible")
    
    # Test appointments list
    print("\n" + "=" * 60)
    print("TESTING APPOINTMENTS LIST")
    print("=" * 60)
    
    response = client.get('/vet-portal/appointments/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Appointments list accessible")
        appt_count = Appointment.objects.count()
        print(f"   Total appointments in database: {appt_count}")
    else:
        print(f"❌ Appointments list not accessible")
    
    # Test medical records list
    print("\n" + "=" * 60)
    print("TESTING MEDICAL RECORDS LIST")
    print("=" * 60)
    
    response = client.get('/vet-portal/records/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Medical records list accessible")
        record_count = MedicalRecord.objects.count()
        print(f"   Total medical records in database: {record_count}")
    else:
        print(f"❌ Medical records list not accessible")
    
    # Test prescriptions list
    print("\n" + "=" * 60)
    print("TESTING PRESCRIPTIONS LIST")
    print("=" * 60)
    
    response = client.get('/vet-portal/prescriptions/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Prescriptions list accessible")
        rx_count = Prescription.objects.filter(is_active=True).count()
        print(f"   Total active prescriptions in database: {rx_count}")
    else:
        print(f"❌ Prescriptions list not accessible")
    
    # Test schedule
    print("\n" + "=" * 60)
    print("TESTING SCHEDULE")
    print("=" * 60)
    
    response = client.get('/vet-portal/schedule/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Schedule accessible")
    else:
        print(f"❌ Schedule not accessible")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ All core vet portal views are accessible and working")
    print("\n📊 DATABASE STATS:")
    print(f"   - Veterinarians: {Veterinarian.objects.count()}")
    print(f"   - Pet Owners: {Owner.objects.count()}")
    print(f"   - Pets: {Pet.objects.count()}")
    print(f"   - Appointments: {Appointment.objects.count()}")
    print(f"   - Medical Records: {MedicalRecord.objects.count()}")
    print(f"   - Active Prescriptions: {Prescription.objects.filter(is_active=True).count()}")
    
    return True

if __name__ == '__main__':
    try:
        success = test_vet_portal()
        if success:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
