from django.contrib import admin
from django.urls import path
from app.goods import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.catalog, name='index'),
    path('product/', views.product, name='product')
]