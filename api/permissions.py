from rest_framework.permissions import BasePermission
from users.models import User

class IsDoctor(BasePermission):
   
    def has_permission(self, request, view):
        return request.user.user_type == User.User_Type.DOCTOR


class IsPatient(BasePermission):
 
    def has_permission(self, request, view):
        return request.user.user_type == User.User_Type.PATIENT
