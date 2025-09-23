from .auth_views import VetLoginView, VetLogoutView
from .dashboard_views import dashboard
from .patient_views import PatientListView, PatientDetailView
from .user_views import user_list, user_detail, user_delete

# Helper function moved to mixins.py