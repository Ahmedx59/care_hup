import django_filters
from django_filters import rest_framework as filters

from users.models import DoctorNurseProfile



class DoctorFilter(filters.FilterSet):
    has_offer = django_filters.BooleanFilter(field_name="offer", method="filter_has_offer")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte") 
    max_price = django_filters.NumberFilter(field_name="price" , lookup_expr="lte")

    class Meta:
        model = DoctorNurseProfile
        fields = ("city", "city__governorate", "has_offer","min_price")


    def filter_has_offer(self, queryset, name, value):
        if value == True:
            return queryset.filter(offer__gt=0)    
        return queryset
    
    # def filter_min_price(self , queryset , name , value):
    #     return queryset.filter(price__gte = value)
    
    # def filter_max_price(self , queryset , name , value):
    #     return queryset.filter(price__lte = value)
