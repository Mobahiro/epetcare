"""
Superadmin API endpoints for mobile app
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from django.db.models import Count
import logging
import secrets
import string

from clinic.models import Pet, Owner, Appointment, MedicalRecord
from vet.models import Veterinarian

logger = logging.getLogger(__name__)


class IsSuperadmin:
    """Permission class to check if user is a superadmin"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Check if user has entry in vet_superadmin table
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM vet_superadmin WHERE user_id = %s AND is_active = TRUE",
                [request.user.id]
            )
            count = cursor.fetchone()[0]
        return count > 0


def superadmin_required(view_func):
    """Decorator to require superadmin access"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check superadmin status
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM vet_superadmin WHERE user_id = %s AND is_active = TRUE",
                [request.user.id]
            )
            count = cursor.fetchone()[0]
        
        if count == 0:
            return Response({'error': 'Superadmin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['POST'])
def superadmin_login(request):
    """Login endpoint for superadmin mobile app"""
    from django.contrib.auth import authenticate
    import hashlib
    import time
    
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Try to authenticate
    user = authenticate(username=username, password=password)
    
    # Also try email login
    if not user:
        try:
            user_by_email = User.objects.get(email__iexact=username)
            user = authenticate(username=user_by_email.username, password=password)
        except User.DoesNotExist:
            pass
    
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({'error': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if superadmin
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.id, s.full_name, s.email 
            FROM vet_superadmin s 
            WHERE s.user_id = %s AND s.is_active = TRUE
        """, [user.id])
        row = cursor.fetchone()
    
    if not row:
        return Response({'error': 'Not authorized as superadmin'}, status=status.HTTP_403_FORBIDDEN)
    
    # Generate a simple token using user info + timestamp hash
    # This is a simple stateless token for the mobile app
    token_data = f"{user.id}:{user.username}:{int(time.time())}"
    token = hashlib.sha256(f"{token_data}:{user.password[:20]}".encode()).hexdigest()
    
    # Store token in session or a simple table
    # For simplicity, we'll use basic auth with username:token pattern
    # The mobile app will store and send this token
    
    return Response({
        'token': f"{user.id}:{token[:32]}",
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'superadmin': {
            'id': row[0],
            'full_name': row[1],
            'email': row[2],
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superadmin_required
def get_dashboard_stats(request):
    """Get dashboard statistics"""
    with connection.cursor() as cursor:
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM vet_veterinarian")
        total_vets = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vet_veterinarian WHERE approval_status != 'approved'")
        pending_vets = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clinic_owner")
        total_owners = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clinic_pet")
        total_pets = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clinic_appointment")
        total_appointments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clinic_medicalrecord")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vet_superadmin")
        total_superadmins = cursor.fetchone()[0]
        
        # Branch stats
        cursor.execute("""
            SELECT branch, COUNT(*) 
            FROM vet_veterinarian 
            GROUP BY branch
        """)
        branch_stats = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
    
    return Response({
        'total_vets': total_vets,
        'pending_vets': pending_vets,
        'total_owners': total_owners,
        'total_pets': total_pets,
        'total_appointments': total_appointments,
        'total_records': total_records,
        'total_superadmins': total_superadmins,
        'branch_stats': branch_stats,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superadmin_required
def list_veterinarians(request):
    """List all veterinarians"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                v.id, u.username, u.email, v.full_name, v.branch, 
                v.specialization, v.license_number, v.access_code, 
                v.approval_status, u.id as user_id, u.is_active
            FROM vet_veterinarian v
            JOIN auth_user u ON v.user_id = u.id
            ORDER BY v.id DESC
        """)
        columns = [col[0] for col in cursor.description]
        vets = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(vets)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@superadmin_required
def approve_veterinarian(request, vet_id):
    """Approve a veterinarian"""
    try:
        vet = Veterinarian.objects.get(id=vet_id)
        vet.approval_status = 'approved'
        
        # Generate access code if not exists
        if not vet.access_code:
            vet.access_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        vet.save()
        return Response({'success': True, 'access_code': vet.access_code})
    except Veterinarian.DoesNotExist:
        return Response({'error': 'Veterinarian not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@superadmin_required
def reject_veterinarian(request, vet_id):
    """Reject a veterinarian"""
    try:
        vet = Veterinarian.objects.get(id=vet_id)
        vet.approval_status = 'rejected'
        vet.save()
        return Response({'success': True})
    except Veterinarian.DoesNotExist:
        return Response({'error': 'Veterinarian not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@superadmin_required
def delete_veterinarian(request, vet_id):
    """Delete a veterinarian"""
    try:
        vet = Veterinarian.objects.get(id=vet_id)
        user_id = vet.user_id
        vet.delete()
        # Also delete the user
        User.objects.filter(id=user_id).delete()
        return Response({'success': True})
    except Veterinarian.DoesNotExist:
        return Response({'error': 'Veterinarian not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superadmin_required
def list_owners(request):
    """List all pet owners"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                o.id, u.username, u.email, o.full_name, o.branch, 
                o.phone, o.address, u.is_active, u.id as user_id
            FROM clinic_owner o
            JOIN auth_user u ON o.user_id = u.id
            ORDER BY o.id DESC
        """)
        columns = [col[0] for col in cursor.description]
        owners = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(owners)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@superadmin_required
def delete_owner(request, owner_id):
    """Delete a pet owner"""
    try:
        owner = Owner.objects.get(id=owner_id)
        user_id = owner.user_id
        owner.delete()
        if user_id:
            User.objects.filter(id=user_id).delete()
        return Response({'success': True})
    except Owner.DoesNotExist:
        return Response({'error': 'Owner not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superadmin_required
def list_pets(request):
    """List all pets"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.id, p.name, p.species, p.breed, p.sex, p.birth_date,
                o.full_name as owner_name, p.weight_kg
            FROM clinic_pet p
            LEFT JOIN clinic_owner o ON p.owner_id = o.id
            ORDER BY p.id DESC
        """)
        columns = [col[0] for col in cursor.description]
        pets = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(pets)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@superadmin_required
def list_superadmins(request):
    """List all superadmins"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.id, u.username, s.email, s.full_name, 
                s.created_at, s.is_active, u.id as user_id
            FROM vet_superadmin s
            JOIN auth_user u ON s.user_id = u.id
            ORDER BY s.id DESC
        """)
        columns = [col[0] for col in cursor.description]
        superadmins = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(superadmins)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@superadmin_required
def create_superadmin(request):
    """Create a new superadmin"""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    full_name = request.data.get('full_name', '').strip()
    
    if not all([username, email, password, full_name]):
        return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if username or email exists
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email__iexact=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Create user
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                first_name=full_name.split()[0] if full_name else '',
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            
            # Create superadmin entry
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vet_superadmin (user_id, full_name, email, is_active, created_at)
                    VALUES (%s, %s, %s, TRUE, NOW())
                """, [user.id, full_name, email])
        
        return Response({'success': True, 'user_id': user.id})
    except Exception as e:
        logger.error(f"Error creating superadmin: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@superadmin_required
def delete_superadmin(request, superadmin_id):
    """Delete a superadmin"""
    # Get superadmin count
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM vet_superadmin")
        count = cursor.fetchone()[0]
    
    if count <= 1:
        return Response({'error': 'Cannot delete the last superadmin'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM vet_superadmin WHERE id = %s", [superadmin_id])
            row = cursor.fetchone()
            if not row:
                return Response({'error': 'Superadmin not found'}, status=status.HTTP_404_NOT_FOUND)
            
            user_id = row[0]
            cursor.execute("DELETE FROM vet_superadmin WHERE id = %s", [superadmin_id])
            
        User.objects.filter(id=user_id).delete()
        return Response({'success': True})
    except Exception as e:
        logger.error(f"Error deleting superadmin: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@superadmin_required
def reset_user_password(request, user_id):
    """Reset a user's password"""
    new_password = request.data.get('password', '')
    
    if not new_password:
        # Generate random password
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    try:
        user = User.objects.get(id=user_id)
        user.password = make_password(new_password)
        user.save()
        return Response({'success': True, 'new_password': new_password})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@superadmin_required  
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({'success': True, 'is_active': user.is_active})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
