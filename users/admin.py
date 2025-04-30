from django.contrib import admin
from users.models import User, PatientProfile, DoctorNurseProfile, SpecialtyDoctor

admin.site.register(User)
admin.site.register(DoctorNurseProfile)
admin.site.register(PatientProfile)
admin.site.register(SpecialtyDoctor)
