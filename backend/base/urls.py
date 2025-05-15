from django.urls import path
from .views import (
    RoomList, RoomDetails, RoomCreate,
    RoomUpdate, RoomDelete, reservation_success,
    CustomLoginView, RegisterView, LogoutView
)
from django.views.generic import TemplateView
urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('room/list', RoomList.as_view(), name='room_list'),
    path('room/<int:idprod>/', RoomDetails.as_view(), name='room_detail'),
    path('room/create/', RoomCreate.as_view(), name='room_create'),
    path('room/update/<int:id>/', RoomUpdate.as_view(), name='room_update'),
    path('room/delete/<int:id>/', RoomDelete.as_view(), name='room_delete'),    path('reservation/success/', reservation_success, name='reservation_success'),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
]
