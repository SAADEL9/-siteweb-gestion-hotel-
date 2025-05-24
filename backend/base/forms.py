from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Room, Reservation, UserProfile
from datetime import date
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=True)
        UserProfile.objects.create(
            user=user,
            phone_number=self.cleaned_data.get('phone_number'),
            is_staff_member=False  # All users registered through the form are regular users
        )
        return user


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = '__all__'


class ReservationForm(forms.ModelForm):
    check_in = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 rounded-lg border-gray-300 focus:ring-primary focus:border-primary'
        })
    )
    check_out = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 rounded-lg border-gray-300 focus:ring-primary focus:border-primary'
        })
    )

    class Meta:
        model = Reservation
        fields = ['check_in', 'check_out']

    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set minimum date for check-in
        today = date.today().isoformat()
        self.fields['check_in'].widget.attrs['min'] = today
        self.fields['check_out'].widget.attrs['min'] = today

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if not self.user:
            raise forms.ValidationError("You must be logged in to make a reservation")

        if not self.room:
            raise forms.ValidationError("Invalid room selection")

        if check_in and check_out:
            today = date.today()
            if check_in < today:
                raise forms.ValidationError("Check-in date cannot be in the past")
            if check_out <= check_in:
                raise forms.ValidationError("Check-out date must be after check-in date")
            
            duration = (check_out - check_in).days
            if duration > 30:
                raise forms.ValidationError("Maximum stay is 30 days")
            if duration <= 0: # Should be caught by check_out <= check_in, but good for clarity
                raise forms.ValidationError("Stay must be for at least one night.")

            # Pass self.instance.pk if the form is bound to an existing instance
            current_res_id = self.instance.pk if self.instance and self.instance.pk else None
            if not self.room.is_available_for_dates(check_in, check_out, current_reservation_id=current_res_id):
                raise forms.ValidationError("Room is not available for these dates")
            
            # Calculate and add total_amount to cleaned_data if we want to access it before save
            # For now, we'll calculate it in the save method.

        return cleaned_data

    def save(self, commit=True):
        if not self.user or not self.room:
            # This state should ideally be prevented by checks in __init__ or clean,
            # but it's a good final guard.
            raise forms.ValidationError("Cannot save reservation: user or room is missing.")
        
        instance = super().save(commit=False)
        instance.user = self.user
        instance.room = self.room

        # Calculate total_amount
        if instance.check_in and instance.check_out and instance.room:
            duration = (instance.check_out - instance.check_in).days
            if duration > 0:
                instance.total_amount = instance.room.price * duration
            else:
                # This case should ideally be caught by form validation (clean method)
                # Set to room price for one night if duration is somehow zero or negative and not caught.
                instance.total_amount = instance.room.price 
        else:
            # This should not happen if form validation is complete.
            # Handle error or set a default if appropriate, though an error is probably better.
            raise forms.ValidationError("Cannot calculate total amount: missing check-in, check-out, or room details.")

        # payment_status defaults to 'pending' in the model.
        
        if commit:
            instance.save()  # This will call the model's save method
        return instance
