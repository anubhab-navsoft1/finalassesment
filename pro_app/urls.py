from django.urls import path
from . import views
urlpatterns = [
    
    path('register/', views.UserRegistrationAPIView.as_view(), name='user-registration'),
    path('login/', views.UserLoginAPIView.as_view(), name='user-login'),
    
    path('lists/', views.ProductListAPIView.as_view(), name = 'product lists'),
    path('lists/add/',views.ProductCreateAPIView.as_view(), name = 'prod update'),
    path('lists/update/<uuid:prod_id>/',views.ProductUpdateAPIView.as_view(), name = 'prod update'),
    path('lists/delete/<uuid:prod_id>/',views.DeleteProductView.as_view(), name = 'prod delete'),
    
    path('api/store/', views.StoreDepotListAPIView.as_view(), name = 'store list'),
     path('api/store/', views.StoreDepotCreateAPIView.as_view(), name = 'store list'),
    path('api/store/<int:pk>/', views.StoreDepotRetrieveUpdateDestroyAPIView.as_view(), name = 'store retrieve'),
    
    path('store/stocks/', views.InventoryListAPIView.as_view(), name = 'inventory create'),
    path('store/stocks/', views.InventoryCreateAPIView.as_view(), name = 'inventory create'),
    path('store/stocks/<int:pk>/', views.InventoryUpdateAPIView.as_view(), name = 'inventory update'),
]