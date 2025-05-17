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
            if (check_out - check_in).days > 30:
                raise forms.ValidationError("Maximum stay is 30 days")
            if not self.room.is_available_for_dates(check_in, check_out):
                raise forms.ValidationError("Room is not available for these dates")

        return cleaned_data

    def save(self, commit=True):
        if not self.user or not self.room:
            raise forms.ValidationError("Cannot save reservation without user and room")
        
        instance = super().save(commit=False)
        instance.user = self.user
        instance.room = self.room
        
        if commit:
            instance.save()
        return instance
