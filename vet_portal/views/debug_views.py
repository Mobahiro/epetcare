from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import os

@login_required
def media_debug(request):
    """
    Debug endpoint to check media configuration and list pet_images files.
    - In development: available to anyone.
    - In production: available to authenticated staff or users with a vet_profile.
    """
    if not settings.DEBUG:
        user = request.user
        if not (getattr(user, 'is_staff', False) or hasattr(user, 'vet_profile')):
            return JsonResponse({"error": "Forbidden"}, status=403)

    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL

    # Get all media files
    pet_images_dir = os.path.join(media_root, 'pet_images')
    media_files = []

    if os.path.exists(pet_images_dir):
        for file in os.listdir(pet_images_dir):
            file_path = os.path.join(pet_images_dir, file)
            if os.path.isfile(file_path):
                rel = f"pet_images/{file}"
                rel_url = f"{media_url}{rel}" if not media_url.endswith(rel) else media_url
                abs_url = request.build_absolute_uri(rel_url) if hasattr(request, 'build_absolute_uri') else rel_url
                media_files.append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'url': rel_url,
                    'absolute_url': abs_url
                })

    return JsonResponse({
        'media_root': media_root,
        'media_url': media_url,
        'media_root_exists': os.path.exists(media_root),
        'pet_images_dir_exists': os.path.exists(pet_images_dir),
        'count': len(media_files),
        'media_files': media_files,
    })


@login_required
def media_upload_form(request):
    """Render a simple form for staff/vets to upload a pet image via API.
    This page uses session auth and CSRF to submit to /vet_portal/api/media/upload/.
    """
    user = request.user
    if not settings.DEBUG and not (getattr(user, 'is_staff', False) or hasattr(user, 'vet_profile')):
        return JsonResponse({"error": "Forbidden"}, status=403)
    return render(request, 'vet_portal/tools/media_upload.html', {})