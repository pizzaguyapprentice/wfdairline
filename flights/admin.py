from django.contrib import admin
from .models import Airport, Plane, Flight, Crew, FlightCrew, Passenger, Ticket, MaintenanceProject, Task

admin.site.register(Airport)
admin.site.register(Plane)
admin.site.register(Flight)
admin.site.register(Crew)
admin.site.register(FlightCrew)
admin.site.register(Passenger)
admin.site.register(Ticket)
admin.site.register(MaintenanceProject)
admin.site.register(Task)