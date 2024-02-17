from django.urls import path
from . import views
from .views import ShopList, MoreDetail, AddNewLocation, AddSales, SalesList


urlpatterns = [
    path('', ShopList.as_view(), name="index"),
    path('detail/<int:pk>/<str:yearmonth>/', MoreDetail.as_view(), name="detail"),
    path('add', AddNewLocation.as_view(), name="add"),
    path('addsales', AddSales.as_view(), name="addsales"),
    path('sales', SalesList.as_view(), name="sales"),
]