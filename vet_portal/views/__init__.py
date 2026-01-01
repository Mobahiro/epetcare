from .auth_views import VetLoginView, vet_logout_view
from .dashboard_views import dashboard, manifest
from .patient_views import PatientListView, PatientDetailView
from .user_views import user_list, user_detail, user_delete
from .records_views import (
	medical_record_create,
	medical_record_update,
	medical_record_delete,
	medical_record_detail,
	medical_record_list,
)
from .prescriptions_views import (
	prescription_create,
	prescription_update,
	prescription_delete,
	prescription_list,
)
from .appointment_views import (
	appointment_list,
	appointment_detail,
	appointment_complete,
	appointment_cancel,
	appointment_create,
)
from .notification_views import (
	mark_notification_read,
	mark_all_notifications_read,
)
from .schedule_views import schedule_list
from .profile_views import vet_profile, profile_update_field

# Helper function moved to mixins.py