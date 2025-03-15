from django.db import models # type: ignore

# Create your models here.
class Governorate(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class City(models.Model):
    name = models.CharField(max_length=100)
    governorate = models.ForeignKey(Governorate, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Hospital(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"