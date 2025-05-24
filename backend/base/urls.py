from django.urls import path
from .views import (
    RoomList, RoomDetails, RoomCreate,
    RoomUpdate, RoomDelete, reservation_success, payment_view, process_payment,
    CustomLoginView, RegisterView, LogoutView, user_reservations,
    StaffReservationsView, delete_reservation_by_staff
)
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('room/list', RoomList.as_view(), name='room_list'),
    path('room/<int:room_id>/', RoomDetails.as_view(), name='room_detail'),
    path('room/create/', RoomCreate.as_view(), name='room_create'),
    path('room/update/<int:id>/', RoomUpdate.as_view(), name='room_update'),
    path('room/delete/<int:id>/', RoomDelete.as_view(), name='room_delete'),    
    path('reservation/success/', reservation_success, name='reservation_success'),
    path('reservations/', user_reservations, name='user_reservations'),
    path('payment/<int:reservation_id>/', payment_view, name='payment_page'),
    path('payment/process/<int:reservation_id>/', process_payment, name='process_payment'),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Staff views
    path('staff/reservations/', StaffReservationsView.as_view(), name='staff_reservations'),
    path('staff/reservation/delete/<int:reservation_id>/', delete_reservation_by_staff, name='staff_delete_reservation'),
]