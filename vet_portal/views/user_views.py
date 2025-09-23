from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from vet.models import Veterinarian
from ..mixins import vet_required

@login_required
@vet_required
def user_list(request):
    """View to list all users in the system"""
    users = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'vet_portal/user_list.html', {'users': users})

@login_required
@vet_required
def user_detail(request, pk):
    """View to show user details"""
    user = get_object_or_404(User, pk=pk)
    vet = Veterinarian.objects.filter(user=user).first()
    return render(request, 'vet_portal/user_detail.html', {'user': user, 'vet': vet})

@login_required
@vet_required
def user_delete(request, pk):
    """View to delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent self-deletion
    if request.user == user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('vet_portal:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' has been deleted successfully.")
        return redirect('vet_portal:user_list')
    
    return render(request, 'vet_portal/user_confirm_delete.html', {'user': user})
