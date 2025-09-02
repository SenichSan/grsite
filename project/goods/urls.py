from django.urls import path

from goods import views
from .views import CategoriesView, CatalogView

app_name = 'goods'

urlpatterns = [
    path('search/', views.CatalogView.as_view(), name='search'),
    # Catalog root (all products) at /catalog/
    path('', CatalogView.as_view(), name='catalog_all'),
    path('<slug:category_slug>/', views.CatalogView.as_view(), name='index'),
    path('product/<slug:product_slug>/', views.ProductView.as_view(), name='product'),
    path('categories/', views.CategoriesView.as_view(), name='categories'),
]
