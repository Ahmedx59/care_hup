from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings


from users.models import User, PatientProfile, DoctorNurseProfile, SpecialtyDoctor


@admin.register(User)
class AdminUser(admin.ModelAdmin):
    list_display = ("username","user_type","email",)
    list_filter = ("username","user_type","email",)
    actions = ("send_activation_email",)
    
    def send_activation_email(self, request, queryset):
        try:
            count = 0
            for obj in queryset:
                send_mail(
                    "Activation Code",
                    f"Welcome {obj.username}\nHere is the activation code: {obj.activation_code}.",
                    settings.EMAIL_HOST_USER,
                    [obj.email],
                    fail_silently=False,
                )
                count += 1

            self.message_user(request, f"✅ Successfully sent activation emails to {count} user(s).")
        except Exception as e:
            self.message_user(request, f" Something wrong happened {e}.")
            

        # cancel doctor activate page and activate the doctor in this endpoint >>>>>>>>>>>>>>>>>


admin.site.register(DoctorNurseProfile)
admin.site.register(PatientProfile)
admin.site.register(SpecialtyDoctor)


