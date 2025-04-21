from django.urls import path
from .views import (
    RoomList, RoomDetails, RoomCreate,
    RoomUpdate, RoomDelete, reservation_success
)

urlpatterns = [
    path('', RoomList.as_view(), name='room_list'),
    path('room/<int:idprod>/', RoomDetails.as_view(), name='room_detail'),
    path('room/create/', RoomCreate.as_view(), name='room_create'),
    path('room/update/<int:id>/', RoomUpdate.as_view(), name='room_update'),
    path('room/delete/<int:id>/', RoomDelete.as_view(), name='room_delete'),
    path('reservation/success/', reservation_success, name='reservation_success'),
]
