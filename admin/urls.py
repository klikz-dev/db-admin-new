from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from vendor.views import InventoryViewSet

from . import views
from vendor.views import OrderViewSet, LineItemViewSet, RoomvoViewSet

router = routers.DefaultRouter()
router.register(r'inventories', InventoryViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'line-items', LineItemViewSet)
router.register(r'roomvo', RoomvoViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/dj-rest-auth/', include('dj_rest_auth.urls'))
]
