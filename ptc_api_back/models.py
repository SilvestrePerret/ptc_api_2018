"""
The models of the objects available through this API are defined here :
Profile, Trip, Segment, Task
"""
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    The profile of users contains every information about them
    """
    traveler = models.OneToOneField(User, on_delete=models.CASCADE)

    nationalities = models.CharField(max_length=255)  # Country names please !
    residence_country = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    visited_countries = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.traveler.username}'



class Trip(models.Model):
    """
    The Trip class represents a whole trip, from a beginning point to an end.
    It is divided into Segments which handle the multiple flights.
    """
    traveler = models.ForeignKey(User, related_name='trips', on_delete=models.CASCADE)

    departure_country = models.CharField(max_length=255)
    departure_airport = models.CharField(max_length=3)
    departure_date_time = models.DateTimeField()
    arrival_country = models.CharField(max_length=255)
    arrival_airport = models.CharField(max_length=3)
    arrival_date_time = models.DateTimeField()
    return_date_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return  f'from {self.departure_airport} to {self.arrival_airport}' +\
                f'(Traveler: {self.traveler.username})'

    def generate_tasks(self):
        """
        Generate the tasks for the first time for the trip.
        Assuming that no tasks are associated with this trip already.

        import TaskFactory here to avoid circular import issue
        """
        from task_factory.task_factory import TaskFactory

        task_factory = TaskFactory(trip=self)
        for task in task_factory.create_tasks():
            task.save()

    def delete_generated_tasks(self):
        """
        Delete every task currently, has to be improved.
        """
        for task in self.tasks.filter(auto=True):
            task.delete()



class Segment(models.Model):
    """
    A part of a trip, often represents a flight from an airport to another. It is designed to handle
     the possible transit cases that are not properly dealt with by the Trip class.
    """
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='segments')

    departure_country = models.CharField(max_length=255)
    departure_airport = models.CharField(max_length=3)
    departure_date_time = models.DateTimeField()
    arrival_country = models.CharField(max_length=255)
    arrival_airport = models.CharField(max_length=3)
    arrival_date_time = models.DateTimeField()
    order = models.IntegerField()


    def __str__(self):
        return  f'{self.order} of Trip {self.trip.id} ' +\
                f'from {self.departure_airport} to {self.arrival_airport}'

    class Meta:
        """
        The segments are ordered by 'order' field.
        """
        ordering = ['order']
        unique_together = ['order', 'trip']



class Task(models.Model):
    """
    A task is an item of the to-do list of the traveler before their departure.
    """
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='tasks')

    title = models.CharField(max_length=255)
    deadline = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    comments = models.TextField(null=True, blank=True)
    auto = models.BooleanField(default=False)
    isVisible = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title} (Trip {self.trip.id}, auto = {self.auto})'
