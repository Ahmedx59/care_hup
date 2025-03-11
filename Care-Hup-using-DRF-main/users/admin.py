from django.contrib import admin
from users.models import User, PatientProfile, DoctorNurseProfile , City , Governorate , SpecialtyDoctor

admin.site.register(User)
admin.site.register(DoctorNurseProfile)
admin.site.register(PatientProfile)
admin.site.register(SpecialtyDoctor)
admin.site.register(Governorate)
admin.site.register(City)
