from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate using either username or email (case-insensitive for email).

    Falls back to the default username behavior. Respects user_can_authenticate.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None or password is None:
            return None

        user = None
        try:
            if '@' in username:
                user = UserModel._default_manager.filter(email__iexact=username).first()
            else:
                # Default username behavior
                user = UserModel._default_manager.get_by_natural_key(username)
        except Exception:
            user = None

        if user is not None and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
