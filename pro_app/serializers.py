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
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category_id.title', read_only=True)
    color_name = serializers.CharField(source='color_code.color', read_only=True)

    class Meta:
        model = ProductDetails
        fields = ['prod_id', 'name', 'sku_number', 'description', 'brand',"brand_name",'category_id', "category_name",'review', 'color_code', 'color_name']
        read_only_fields = ['prod_id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['brand_name'] = instance.brand.name
        data['category_name'] = instance.category_id.title
        data['color_name'] = instance.color_code.color
        return data

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