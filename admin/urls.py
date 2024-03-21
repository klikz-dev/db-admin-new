from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from vendor.views import InventoryViewSet

from . import views

router = routers.DefaultRouter()
router.register(r'inventories', InventoryViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/dj-rest-auth/', include('dj_rest_auth.urls'))
]
