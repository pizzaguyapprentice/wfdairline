from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Airport(models.Model):
    iata_code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.iata_code} - {self.name}"

    class Meta:
        ordering = ['iata_code']


class Plane(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'In Maintenance'),
    ]
    
    model = models.CharField(max_length=100)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.model} (Capacity: {self.capacity})"

    class Meta:
        ordering = ['model']


class Flight(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('boarding', 'Boarding'),
        ('in_flight', 'In Flight'),
        ('landed', 'Landed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]
    
    plane = models.ForeignKey(Plane, on_delete=models.PROTECT, related_name='flights')
    departure_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='departing_flights')
    arrival_airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name='arriving_flights')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        return f"{self.departure_airport.iata_code}-{self.arrival_airport.iata_code} ({self.departure_time.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        ordering = ['-departure_time']

    def available_seats(self):
        return self.plane.capacity - self.tickets.count()


class Crew(models.Model):
    POSITION_CHOICES = [
        ('pilot', 'Pilot'),
        ('co_pilot', 'Co-Pilot'),
        ('flight_attendant', 'Flight Attendant'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='crew_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        ordering = ['surname', 'name']


class FlightCrew(models.Model):
    ROLE_CHOICES = [
        ('pilot', 'Pilot'),
        ('co_pilot', 'Co-Pilot'),
        ('flight_attendant', 'Flight Attendant'),
    ]
    
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='crew_assignments')
    crew = models.ForeignKey(Crew, on_delete=models.PROTECT, related_name='flight_assignments')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('flight', 'crew')

    def __str__(self):
        return f"{self.crew} - {self.flight}"


class Passenger(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        ordering = ['surname', 'name']


class Ticket(models.Model):
    CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]
    
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='tickets')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='tickets')
    seat = models.CharField(max_length=10)
    class_type = models.CharField(max_length=20, choices=CLASS_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('flight', 'seat')
        ordering = ['seat']

    def __str__(self):
        return f"{self.passenger} - {self.flight} - Seat {self.seat}"


class MaintenanceProject(models.Model):
    plane = models.ForeignKey(Plane, on_delete=models.CASCADE, related_name='maintenance_projects')
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.plane.model} - {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['-start_date']


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    maintenance_project = models.ForeignKey(MaintenanceProject, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_tasks')

    def __str__(self):
        return f"{self.maintenance_project} - {self.description[:50]}"

    class Meta:
        ordering = ['status', '-maintenance_project']