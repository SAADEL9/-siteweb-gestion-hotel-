from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .forms import RoomForm, ReservationForm
from .models import Room


class RoomList(View):
    def get(self, request):
        rooms = Room.objects.all()
        return render(request, 'listRooms.html', {'rooms': rooms})


class RoomDetails(View):
    def get(self, request, idprod):
        room = get_object_or_404(Room, id=idprod)
        form = ReservationForm()
        return render(request, 'RoomDetails.html', {'room': room, 'form': form})

    #@method_decorator(login_required)
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



class RoomCreate(View):
    def get(self, request):
        form = RoomForm()
        return render(request, 'RoomCreate.html', {'form': form})

    def post(self, request):
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('')
        return render(request, 'RoomCreate.html', {'form': form})


#@method_decorator(login_required, name='dispatch')
class RoomUpdate(View):
    def get(self, request, id):
        room = get_object_or_404(Room, id=id)
        form = RoomForm(instance=room)
        return render(request, 'RoomCreate.html', {'form': form})

    def post(self, request, id):
        room = get_object_or_404(Room, id=id)
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/rooms/')
        return render(request, 'RoomCreate.html', {'form': form})


#@method_decorator(login_required, name='dispatch')
class RoomDelete(View):
    def get(self, request, id):
        room = get_object_or_404(Room, id=id)
        room.delete()
        return HttpResponseRedirect('')


def reservation_success(request):
    return render(request, 'success.html')
