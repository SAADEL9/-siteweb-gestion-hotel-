from urllib import request
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import login, logout, authenticate
from django.core.exceptions import ValidationError
from django.contrib import messages
from datetime import date, datetime, timedelta
from django.utils import timezone
from .forms import RoomForm, ReservationForm, UserRegistrationForm
from .models import Room, UserProfile, Reservation
from datetime import datetime

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = 'room_list'

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class RegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        return render(request, 'register.html', {'form': form})


class IsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
        
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return redirect('room_list')


class RoomList(View):
    def get(self, request):
        rooms = Room.objects.all()
        
        # Get search parameters
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        room_type = request.GET.get('room_type')
        
        # Filter rooms based on search criteria
        available_rooms = []
        if check_in and check_out:
            try:
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                
                if check_out_date <= check_in_date:
                    messages.error(request, "Check-out date must be after check-in date")
                else:
                    # Check each room's availability for the selected dates
                    for room in rooms:
                        is_available = room.is_available_for_dates(check_in_date, check_out_date)
                        # Add availability status to the room object
                        room.is_available = is_available
                        if is_available:
                            available_rooms.append(room)
                    rooms = available_rooms
            except ValueError:
                messages.error(request, "Invalid date format")
        else:
            # If no dates selected, mark all rooms as needing date selection
            for room in rooms:
                room.is_available = None
        
        if room_type:
            rooms = [room for room in rooms if room.room_type == room_type]
        
        context = {
            'rooms': rooms,
            'check_in': check_in,
            'check_out': check_out,
            'room_type': room_type,
            'room_types': Room.ROOM_TYPES,
            'today': date.today().isoformat(),
        }
        return render(request, 'listRooms.html', context)

def home(request):
    context = {
        'today': date.today(),
    }
    return render(request, 'home.html', context)
    
@method_decorator(login_required, name='dispatch')
# views.py


class RoomDetails(View):
    def get(self, request, room_id):
        room = get_object_or_404(Room, pk=room_id)
        reservations = room.reservation_set.all()
        blocked_dates = []

        for reservation in reservations:
            current = reservation.check_in
            while current <= reservation.check_out:
                blocked_dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

        return render(request, 'RoomDetails.html', {
            'room': room,
            'blocked_dates': blocked_dates,
            'today': datetime.today().strftime('%Y-%m-%d'),
        })


@method_decorator(login_required, name='dispatch')
class RoomCreate(IsStaffMixin, View):
    def get(self, request):
        form = RoomForm()
        return render(request, 'RoomCreate.html', {'form': form})

    def post(self, request):
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('room_list')
        return render(request, 'RoomCreate.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class RoomUpdate(IsStaffMixin, View):
    def get(self, request, id):
        room = get_object_or_404(Room, id=id)
        form = RoomForm(instance=room)
        return render(request, 'RoomCreate.html', {'form': form})

    def post(self, request, id):
        room = get_object_or_404(Room, id=id)
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/room/list')
        return render(request, 'listRoom.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class RoomDelete(IsStaffMixin, View):
    def get(self, request, id):
        room = get_object_or_404(Room, id=id)
        room.delete()
        return HttpResponseRedirect('')


@login_required
def reservation_success(request):
    # Get the user's most recent reservation
    latest_reservation = Reservation.objects.filter(user=request.user).order_by('-created_at').first()
    return render(request, 'reservation_success.html', {'reservation': latest_reservation})

@login_required
def user_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-check_in')
    return render(request, 'user_reservations.html', {'reservations': reservations})
