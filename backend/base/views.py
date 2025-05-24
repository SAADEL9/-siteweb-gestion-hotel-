from urllib import request
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
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
import uuid
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

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
        
        # Pass an empty form instance for the GET request
        form = ReservationForm(room=room, user=request.user if request.user.is_authenticated else None)

        return render(request, 'RoomDetails.html', {
            'room': room,
            'form': form, # Add form to context
            'blocked_dates': blocked_dates,
            'today': datetime.today().strftime('%Y-%m-%d'),
        })

    @method_decorator(login_required)
    def post(self, request, room_id):
        room = get_object_or_404(Room, pk=room_id)
        form = ReservationForm(request.POST, room=room, user=request.user)

        if form.is_valid():
            try:
                reservation = form.save() # Save the reservation instance (it now has total_amount and default payment_status)
                # Instead of redirecting to reservation_success, redirect to the new payment page
                messages.info(request, 'Please complete your payment to confirm the reservation.') # Optional message
                return redirect('payment_page', reservation_id=reservation.id)
            except ValidationError as e:
                messages.error(request, f"Booking failed: {', '.join(e.messages) if hasattr(e, 'messages') else e}")
        else:
            # Form is not valid, errors will be in form.errors
            # messages.error(request, 'Please correct the errors below.') # Optional, form errors are usually shown by fields
            pass # Fall through to re-render the page with the form containing errors
        
        # If form is invalid or save failed with ValidationError, re-render the page
        # We need all context variables that the GET request uses
        reservations = room.reservation_set.all()
        blocked_dates = []
        for res in reservations: # Renamed to avoid conflict with 'reservation' from form.save() context
            current = res.check_in
            while current <= res.check_out:
                blocked_dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)

        return render(request, 'RoomDetails.html', {
            'room': room,
            'form': form, # Pass the form with errors
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

@login_required
def payment_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)

    if reservation.payment_status == Reservation.PAYMENT_STATUS_SUCCEEDED:
        messages.info(request, "This reservation has already been paid.")
        return redirect('reservation_success')

    # Calculate number of nights for display
    duration = (reservation.check_out - reservation.check_in).days
    number_of_nights = duration if duration > 0 else 1

    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=int(reservation.total_amount * 100),  # Convert to cents
            currency='usd',
            metadata={
                'reservation_id': reservation.id,
                'room_number': reservation.room.room_number,
                'check_in': reservation.check_in.isoformat(),
                'check_out': reservation.check_out.isoformat(),
            }
        )

        context = {
            'reservation': reservation,
            'room': reservation.room,
            'number_of_nights': number_of_nights,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
            'client_secret': intent.client_secret,
        }
        return render(request, 'payment.html', context)
    except Exception as e:
        messages.error(request, f"Error creating payment: {str(e)}")
        return redirect('room_detail', room_id=reservation.room.id)

@login_required
def process_payment(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
        
        try:
            # Get the payment intent from the request
            payment_intent_id = request.POST.get('payment_intent_id')
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                # Update reservation status
                reservation.payment_status = Reservation.PAYMENT_STATUS_SUCCEEDED
                reservation.payment_date = timezone.now()
                reservation.payment_intent_id = payment_intent_id
                reservation.save()
                
                messages.success(request, 'Payment successful! Your reservation is confirmed.')
                return redirect('reservation_success')
            else:
                messages.error(request, 'Payment failed. Please try again.')
                return redirect('payment_page', reservation_id=reservation_id)
                
        except Exception as e:
            messages.error(request, f'Payment processing error: {str(e)}')
            return redirect('payment_page', reservation_id=reservation_id)
    else:
        return redirect('payment_page', reservation_id=reservation_id)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_staff), name='dispatch')
class StaffReservationsView(View):
    template_name = 'staff_reservations.html'

    def get(self, request, *args, **kwargs):
        # Order by most recent first, then by check-in date
        reservations = Reservation.objects.all().order_by('-created_at', '-check_in')
        context = {
            'reservations': reservations
        }
        return render(request, self.template_name, context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_reservation_by_staff(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    if request.method == 'POST':
        room_number = reservation.room.room_number # Get details before deleting
        user_name = reservation.user.username
        reservation.delete()
        messages.success(request, f'Reservation for Room {room_number} by {user_name} has been deleted.')
        return redirect('staff_reservations')
    else:
        # If accessed via GET, perhaps show a confirmation page or just redirect
        messages.warning(request, 'Deletion must be confirmed via POST request.')
        return redirect('staff_reservations')