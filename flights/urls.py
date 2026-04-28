from django.urls import path
from . import views

urlpatterns = [
    path('', views.flight_list, name='flight_list'),
    path('book/<int:flight_id>/', views.book_ticket, name='book_ticket'),
    path('crew/', views.crew_flights, name='crew_flights'),
    path('maintenance/', views.maintenance_projects, name='maintenance_projects'),
    path('task/<int:task_id>/', views.task_update, name='task_update'),
    path('project/<int:project_id>/add-task/', views.create_task, name='create_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    path('project/create/', views.create_project, name='create_project'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('flight/<int:flight_id>/assign/', views.assign_self, name='assign_self'),
    path('flight/<int:flight_id>/unassign/', views.unassign_self, name='unassign_self'),
]