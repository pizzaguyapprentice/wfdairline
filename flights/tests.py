from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from flights.models import (
    Airport,Crew,Flight,FlightCrew,MaintenanceProject,Passenger,Plane,Task,Ticket,
)


class AirlineBaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.passenger_user = User.objects.create_user(
            username="passenger1",
            password="pass123"
        )
        cls.crew_user = User.objects.create_user(
            username="crew1",
            password="pass123"
        )
        cls.staff_user = User.objects.create_user(
            username="staff1",
            password="pass123",
            is_staff=True
        )

        cls.passenger = Passenger.objects.create(
            user=cls.passenger_user,
            name="Billy",
            surname="King",
            age=31
        )

        cls.crew = Crew.objects.create(
            user=cls.crew_user,
            name="Silo",
            surname="Jerry",
            position="pilot"
        )

        cls.airport1 = Airport.objects.create(
            iata_code="DUB",
            name="Dublin Airport",
            city="Dublin",
            country="Ireland"
        )
        cls.airport2 = Airport.objects.create(
            iata_code="ODL",
            name="London Airport",
            city="London",
            country="UK"
        )

        cls.plane = Plane.objects.create(
            model="Boeing 747",
            capacity=180,
            status="active"
        )

        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=2)

        cls.flight = Flight.objects.create(
            plane=cls.plane,
            departure_airport=cls.airport1,
            arrival_airport=cls.airport2,
            departure_time=departure,
            arrival_time=arrival,
            status="scheduled"
        )

    def login_passenger(self):
        self.client.login(username="passenger1", password="pass123")

    def login_crew(self):
        self.client.login(username="crew1", password="pass123")

    def login_staff(self):
        self.client.login(username="staff1", password="pass123")


class FlightAccessTests(AirlineBaseTestCase):
    def test_passenger_can_view_flights(self):
        self.login_passenger()
        response = self.client.get(reverse("flight_list"))
        self.assertEqual(response.status_code, 200)

    def test_crew_cannot_view_flights_page(self):
        self.login_crew()
        response = self.client.get(reverse("flight_list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("crew_flights"))

    def test_staff_cannot_view_flights_page(self):
        self.login_staff()
        response = self.client.get(reverse("flight_list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("maintenance_projects"))


class TicketTests(AirlineBaseTestCase):
    def test_passenger_can_book_ticket(self):
        self.login_passenger()
        response = self.client.post(reverse("book_ticket", args=[self.flight.id]), {
            "seat": "12A"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 1)

        ticket = Ticket.objects.first()
        self.assertEqual(ticket.passenger, self.passenger)
        self.assertEqual(ticket.flight, self.flight)
        self.assertEqual(ticket.seat, "12A")
        self.assertEqual(ticket.class_type, "economy")

    def test_crew_cannot_book_ticket(self):
        self.login_crew()
        response = self.client.post(reverse("book_ticket", args=[self.flight.id]), {
            "seat": "13A"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 0)


class CrewAssignmentTests(AirlineBaseTestCase):
    def test_crew_can_assign_self_to_flight(self):
        self.login_crew()
        response = self.client.post(reverse("assign_self", args=[self.flight.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FlightCrew.objects.count(), 1)

        assignment = FlightCrew.objects.first()
        self.assertEqual(assignment.flight, self.flight)
        self.assertEqual(assignment.crew, self.crew)
        self.assertEqual(assignment.role, "pilot")

    def test_crew_assignment_is_not_duplicated(self):
        self.login_crew()
        self.client.post(reverse("assign_self", args=[self.flight.id]))
        self.client.post(reverse("assign_self", args=[self.flight.id]))
        self.assertEqual(FlightCrew.objects.count(), 1)

    def test_crew_can_unassign_self_from_flight(self):
        FlightCrew.objects.create(
            flight=self.flight,
            crew=self.crew,
            role="pilot"
        )

        self.login_crew()
        response = self.client.post(reverse("unassign_self", args=[self.flight.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FlightCrew.objects.count(), 0)

    def test_passenger_cannot_assign_self_to_flight(self):
        self.login_passenger()
        response = self.client.post(reverse("assign_self", args=[self.flight.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FlightCrew.objects.count(), 0)


class MaintenanceProjectTests(AirlineBaseTestCase):
    def test_staff_can_create_project(self):
        self.login_staff()
        response = self.client.post(reverse("create_project"), {
            "plane": self.plane.id,
            "start_date": "2011-01-01",
            "end_date": "2011-01-10"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MaintenanceProject.objects.count(), 1)

        project = MaintenanceProject.objects.first()
        self.assertEqual(project.plane, self.plane)

    def test_crew_cannot_create_project(self):
        self.login_crew()
        response = self.client.post(reverse("create_project"), {
            "plane": self.plane.id,
            "start_date": "2011-01-01",
            "end_date": "2011-01-10"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MaintenanceProject.objects.count(), 0)

    def test_staff_can_delete_project(self):
        project = MaintenanceProject.objects.create(
            plane=self.plane,
            start_date="2011-01-01",
            end_date="2011-01-10"
        )

        self.login_staff()
        response = self.client.post(reverse("delete_project", args=[project.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MaintenanceProject.objects.count(), 0)


class TaskTests(AirlineBaseTestCase):
    def setUp(self):
        super().setUp()
        self.project = MaintenanceProject.objects.create(
            plane=self.plane,
            start_date="2011-01-01",
            end_date="2011-01-10"
        )

    def test_staff_can_create_task(self):
        self.login_staff()
        response = self.client.post(reverse("create_task", args=[self.project.id]), {
            "description": "Check engine"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 1)

        task = Task.objects.first()
        self.assertEqual(task.maintenance_project, self.project)
        self.assertEqual(task.description, "Check engine")
        self.assertEqual(task.status, "pending")

    def test_staff_can_update_task(self):
        task = Task.objects.create(
            maintenance_project=self.project,
            description="Check engine",
            status="pending"
        )

        self.login_staff()
        response = self.client.post(reverse("task_update", args=[task.id]), {
            "status": "completed"
        })
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_staff_can_delete_task(self):
        task = Task.objects.create(
            maintenance_project=self.project,
            description="Check engine",
            status="pending"
        )

        self.login_staff()
        response = self.client.post(reverse("delete_task", args=[task.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)

    def test_passenger_cannot_create_task(self):
        self.login_passenger()
        response = self.client.post(reverse("create_task", args=[self.project.id]), {
            "description": "Should not work"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)