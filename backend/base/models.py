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

    # Amenities
    has_balcony = models.BooleanField(default=False)
    has_sea_view = models.BooleanField(default=False)

    image1 = models.ImageField(upload_to='room_images/', blank=True, null=True, verbose_name="Image 1")
    image2 = models.ImageField(upload_to='room_images/', blank=True, null=True, verbose_name="Image 2")
    image3 = models.ImageField(upload_to='room_images/', blank=True, null=True, verbose_name="Image 3")
    image4 = models.ImageField(upload_to='room_images/', blank=True, null=True, verbose_name="Image 4")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.get_room_type_display()})"

    def is_available_for_dates(self, check_in, check_out, current_reservation_id=None):
        # Build a query for potentially conflicting reservations
        conflicting_reservations = self.reservation_set.filter(
            check_in__lt=check_out,  # Starts before the proposed booking ends
            check_out__gt=check_in   # Ends after the proposed booking starts
        )

        if current_reservation_id:
            # Exclude the current reservation itself from the conflict check
            conflicting_reservations = conflicting_reservations.exclude(pk=current_reservation_id)
        
        return not conflicting_reservations.exists()

    def get_next_available_date(self):
        latest_reservation = self.reservation_set.filter(check_out__gt=timezone.now().date()).order_by('-check_out').first()
        if latest_reservation:
            return latest_reservation.check_out
        return timezone.now().date()


class Reservation(models.Model):
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_SUCCEEDED = 'succeeded'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_SUCCEEDED, 'Succeeded'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Payment related fields
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING
    )
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reservation by {self.user.username} for Room {self.room.room_number}"

    def clean(self):
        if self.check_in and self.check_out:
            if self.check_in < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")
            if self.check_out <= self.check_in:
                raise ValidationError("Check-out date must be after check-in date")
            
            if self.room_id:
                # Pass self.pk (which can be None for new instances) to exclude current reservation if it exists
                if not self.room.is_available_for_dates(self.check_in, self.check_out, current_reservation_id=self.pk):
                    raise ValidationError("Room is not available for these dates (model clean)")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
