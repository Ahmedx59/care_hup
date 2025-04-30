from django.contrib import admin
from .models import *

from hospital.models import City

class CityInline(admin.TabularInline):
    model = City

    
@admin.register(Governorate)
class AdminGovernorate(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)
    inlines = (CityInline,)

# admin.site.register(Governorate)
admin.site.register(City)
admin.site.register(Hospital)
admin.site.register(Department)
