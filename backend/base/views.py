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
from .forms import RoomForm, ReservationForm, UserRegistrationForm
from .models import Room, UserProfile


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
        return render(request, 'listRooms.html', {'rooms': rooms})

def home(request):
    return render(request,'home.html')
    
class RoomDetails(View):
    def get(self, request, idprod):
        room = get_object_or_404(Room, id=idprod)
        form = ReservationForm()
        return render(request, 'RoomDetails.html', {'room': room, 'form': form})

    def post(self, request, idprod):
        room = get_object_or_404(Room, id=idprod)
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.room = room
            reservation.save()
            room.is_available = False
            room.save()
            return redirect('reservation_success')
        return render(request, 'RoomDetails.html', {'room': room, 'form': form})


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


def reservation_success(request):
    return render(request, 'success.html')
