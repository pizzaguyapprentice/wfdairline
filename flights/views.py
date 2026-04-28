from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Flight, Ticket, FlightCrew, MaintenanceProject, Task, Plane
from django.views.decorators.http import require_POST

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Flight, FlightCrew

@login_required
def crew_flights(request):
    if not hasattr(request.user, 'crew_profile'):
        return redirect('flight_list')

    crew = request.user.crew_profile

    assignments = FlightCrew.objects.filter(crew=crew)
    flights = Flight.objects.all()

    assigned_flight_ids = list(
        assignments.values_list('flight_id', flat=True)
    )

    return render(request, 'flights/crew_flights.html', {
        'assignments': assignments,
        'flights': flights,
        'assigned_flight_ids': assigned_flight_ids,
        'role': 'crew'
    })


@login_required
def assign_self(request, flight_id):
    if request.method != 'POST':
        return redirect('crew_flights')

    if not hasattr(request.user, 'crew_profile'):
        return redirect('flight_list')

    crew = request.user.crew_profile
    flight = get_object_or_404(Flight, id=flight_id)

    FlightCrew.objects.get_or_create(
        flight=flight,
        crew=crew,
        defaults={'role': crew.position}
    )

    return redirect('crew_flights')


@login_required
def unassign_self(request, flight_id):
    if request.method != 'POST':
        return redirect('crew_flights')

    if not hasattr(request.user, 'crew_profile'):
        return redirect('flight_list')

    crew = request.user.crew_profile

    assignment = FlightCrew.objects.filter(
        flight_id=flight_id,
        crew=crew
    ).first()

    if assignment:
        assignment.delete()

    return redirect('crew_flights')

@login_required
def delete_task(request, task_id):
    if not request.user.is_staff:
        return redirect('flight_list')
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
    return redirect('maintenance_projects')

@login_required
def create_task(request, project_id):
    if not request.user.is_staff:
        return redirect('flight_list')
    project = get_object_or_404(MaintenanceProject, id=project_id)
    if request.method == 'POST':
        description = request.POST.get('description')
        Task.objects.create(
            maintenance_project=project,
            description=description,
            status='pending',
            assigned_to=request.user
        )
    return redirect('maintenance_projects')


def get_role(user):
    if hasattr(user, 'passenger_profile'):
        return 'passenger'
    if hasattr(user, 'crew_profile'):
        return 'crew'
    if user.is_staff:
        return 'maintenance'
    return None

@login_required
def flight_list(request):
    if hasattr(request.user, 'passenger_profile'):
        flights = Flight.objects.all()
        return render(request, 'flights/flight_list.html', {
            'flights': flights,
            'role': 'passenger'
        })

    elif hasattr(request.user, 'crew_profile'):
        return redirect('crew_flights')

    elif request.user.is_staff:
        return redirect('maintenance_projects')

    return redirect('login')

@login_required
def book_ticket(request, flight_id):
    if not hasattr(request.user, 'passenger_profile'):
        return redirect('flight_list')

    flight = get_object_or_404(Flight, id=flight_id)
    passenger = request.user.passenger_profile

    if request.method == 'POST':
        seat = request.POST.get('seat')
        Ticket.objects.create(
            passenger=passenger,
            flight=flight,
            seat=seat,
            class_type='economy',
            price=100
        )
        return redirect('flight_list')

    role = get_role(request.user)

    return render(request, 'flights/book_ticket.html', {
        'flight': flight,
        'role': role
    })



@login_required
def maintenance_projects(request):
    if not request.user.is_staff:
        return redirect('flight_list')

    projects = MaintenanceProject.objects.all()
    planes = Plane.objects.all()

    return render(request, 'flights/maintenance_projects.html', {
        'projects': projects,
        'planes': planes,
        'role': 'maintenance'
    })


@login_required
def task_update(request, task_id):
    if not request.user.is_staff:
        return redirect('flight_list')

    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        task.status = request.POST.get('status')
        task.save()
        return redirect('maintenance_projects')

    return render(request, 'flights/task_update.html', {
        'task': task,
        'role': 'maintenance'
    })

@login_required
def create_project(request):
    if not request.user.is_staff:
        return redirect('flight_list')

    if request.method == 'POST':
        plane_id = request.POST.get('plane')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        plane = get_object_or_404(Plane, id=plane_id)

        MaintenanceProject.objects.create(
            plane=plane,
            start_date=start_date,
            end_date=end_date
        )

    return redirect('maintenance_projects')

@login_required
def delete_project(request, project_id):
    if not request.user.is_staff:
        return redirect('flight_list')

    project = get_object_or_404(MaintenanceProject, id=project_id)

    if request.method == 'POST':
        project.delete()

    return redirect('maintenance_projects')
