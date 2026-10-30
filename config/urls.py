from django.urls import path

from inventory import views

urlpatterns = [
    path("orders/<str:reference>/box/", views.order_box, name="order-box"),
]
