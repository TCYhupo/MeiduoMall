from django.contrib.auth.backends import ModelBackend
from .models import User
from django.http import JsonResponse

class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            try:
                user = User.objects.get(password=password)
            except Exception as e:
                return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user