from rest_framework import serializers
from .models import CategoryOfProducts, ProductDetails,Brand, prod_col, StoreDepotModel, InventoryDEpartmentModel
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class CategoryOfProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryOfProducts
        fields = ['id', 'title', 'description']
        
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['name', 'description']

class ProdColSerializer(serializers.ModelSerializer):
    class Meta:
        model = prod_col
        fields = ['id', 'color', 'description']

class ProductDetailsSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = ProductDetails
        fields = ['name', 'sku_number', 'description', 'review','brand', 'category_id', 'color_code']

class StoreDepotSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = StoreDepotModel
        fields = '__all__'


class InventoryDEpartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryDEpartmentModel
        fields = ['store_id', 'product_id', 'quantity', 'is_available']
        
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        # Extract the password from validated data
        password = validated_data.pop('password')

        # Create a new user with a hashed password
        user = User.objects.create_user(**validated_data, password=password)

        return user
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        
# class OrderItemSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = OrderItems
#         fields = "__all__"