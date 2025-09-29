from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
import subprocess

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def deploy_hook(request):
    """
    Handle deploy webhook from Render
    """
    # Validate the request (you can add your own validation if needed)
    key = request.GET.get('key')
    if key != 'Zay8YidqwKg':
        return HttpResponseForbidden("Invalid key")
    
    try:
        # Log the deploy hook trigger
        logger.info("Deploy hook triggered")
        
        # Get the payload
        try:
            payload = json.loads(request.body)
            logger.info(f"Deploy payload: {payload}")
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in deploy hook payload")
            payload = {}
        
        # You can perform additional actions here if needed
        # For example, clear cache, run additional scripts, etc.
        
        # Return a success response
        return HttpResponse("Deploy hook processed successfully", status=200)
    
    except Exception as e:
        logger.error(f"Error in deploy hook: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500)