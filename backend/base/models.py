from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_staff_member = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ]

    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    floor = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    number_of_beds = models.IntegerField(default=1)
    has_balcony = models.BooleanField(default=False)
    has_sea_view = models.BooleanField(default=False)
    image = models.ImageField(upload_to='room_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"

    def is_available_for_dates(self, check_in, check_out):
        # Check for overlapping reservations that are in the future
        future_reservations = self.reservation_set.filter(
            check_out__gt=timezone.now().date()
        ).order_by('check_in')

        # If there are no future reservations, the room is available
        if not future_reservations.exists():
            return True

        for reservation in future_reservations:
            # Allow booking if it starts exactly when another booking ends
            if check_in == reservation.check_out:
                # Check if there are any other reservations starting on check_in
                if not self.reservation_set.filter(check_in=check_in).exists():
                    continue
            
            # Check for any overlap
            if (check_in < reservation.check_out and 
                check_out > reservation.check_in):
                return False
        
        return True

    def get_next_available_date(self):
        latest_reservation = self.reservation_set.filter(check_out__gt=timezone.now().date()).order_by('-check_out').first()
        if latest_reservation:
            return latest_reservation.check_out
        return timezone.now().date()


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation by {self.user.username} for Room {self.room.room_number}"

    def clean(self):
        if self.check_in and self.check_out:
            if self.check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")
            if self.check_out <= self.check_in:
                raise ValidationError("Check-out date must be after check-in date")
            if not self.room.is_available_for_dates(self.check_in, self.check_out):
                raise ValidationError("Room is not available for these dates")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
