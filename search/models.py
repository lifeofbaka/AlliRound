from django.db import models
from django.utils import timezone

# Create your models here.

# Flight table keeps track of user defined searches 
class Flight(models.Model):
    departure_text = models.CharField(max_length=4)
    arrival_text = models.CharField(max_length=4)
    departure_date = models.DateField()
    return_date = models.DateField()
    search_date = models.DateTimeField(default=timezone.now())


    def __str__(self) -> str:
        return self.departure_text + " - " + self.arrival_text

# The items of this table are an account of the breakdown of all flights involved in a Flight table route (All backend searches that makeup a Flight)
class FlightSearchBreakdown(models.Model):
    departure_text = models.CharField(max_length=4)
    arrival_text = models.CharField(max_length=4)
    departure_date = models.DateField()
    return_date = models.DateField()
    search_date = models.DateTimeField(default=timezone.now())

# Cache of all Flight Breakdowns search results 
class FlightSearchCache(models.Model):
    # query_hash = models.CharField(max_length=32, unique=True)
    origin_code = models.CharField(max_length=4)
    destination_code = models.CharField(max_length=4)
    origin_depart_time = models.CharField(max_length=50)
    destination_arrival_time = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    main_cabin_min = models.CharField(max_length=50)
    premium_cabin_min = models.CharField(max_length=50)
    search_date = models.DateTimeField(default=timezone.now())

    
    
   
