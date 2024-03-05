from django.urls import path
from . import views
urlpatterns = [
    path('',views.store,name='store'),
    path(route ='<slug:category_slug>/',view=views.store,name='products_by_category'),
    path(route ='<slug:category_slug>/<slug:product_slug>/',view=views.product_detail,name='products_detail'),
]