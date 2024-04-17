from rest_framework import generics, status
from django.db import transaction
from rest_framework.response import Response
from .models import CategoryOfProducts, prod_col, ProductDetails, Brand, StoreDepotModel, InventoryDEpartmentModel
from .serializers import CategoryOfProductsSerializer,UserLoginSerializer, UserRegistrationSerializer,UserSerializer,ProdColSerializer, BrandSerializer, ProductDetailsSerializer, StoreDepotSerializer, InventoryDEpartmentSerializer
from random import randint
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from .permissions import ReadOnlyOrAdminPermission
from rest_framework.permissions import IsAuthenticated, IsAdminUser
import pandas as pd
from django.http import HttpResponse

class UserRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailsAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
      
class ProductListAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get list of products",
        operation_description="Retrieve a list of products optionally filtered by search query and sorted.",
        responses={200: ProductDetailsSerializer(many=True)},
    )
    def get(self, request):
        search_query = request.query_params.get('search', None)
        sort_by = request.query_params.get('sort_by', None)

        if search_query:
            products = ProductDetails.objects.filter(name__icontains=search_query) | ProductDetails.objects.filter(brand__name__icontains=search_query)
        else:
            products = ProductDetails.objects.all()

        if sort_by:
            products = products.order_by(sort_by)

        serializer = ProductDetailsSerializer(products, many=True)

        return Response({"data" : serializer.data,})
    
class ProductCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    @transaction.atomic
    @swagger_auto_schema(
        operation_summary="Create a new product",
        operation_description="Create a new product with category, brand, color, and other details.",
        request_body=ProductDetailsSerializer,
        responses={
            201: openapi.Response(
                description="Product created successfully",
                schema=ProductDetailsSerializer,
            ),
            400: "Bad Request"
        },
    )
    def post(self, request):
        data = request.data
        
        category_data = data.get('category', {})
        category_serializer = CategoryOfProductsSerializer(data=category_data)
        
        if category_serializer.is_valid():
            try:
                existing_category = CategoryOfProducts.objects.get(title=category_data['title'])
                category_instance = existing_category
            except CategoryOfProducts.DoesNotExist:
                category_serializer.is_valid(raise_exception=True)
                category_instance = category_serializer.save()
        else:
            return Response(category_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract brand data from request
        brand_data = data.get('brand', {})
        brand_serializer = BrandSerializer(data=brand_data)
        
        if brand_serializer.is_valid():
            try:
                existing_brand = Brand.objects.get(name=brand_data['name'])
                brand_instance = existing_brand
                brand_message = 'Brand already exists.'
            except Brand.DoesNotExist:
                brand_serializer.is_valid(raise_exception=True)
                brand_instance = brand_serializer.save()
                brand_message = 'New brand created.'
        else:
            return Response(brand_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_data = data.get('product', {})
        product_name = product_data.get('name', '')
        sku_number = product_data.get('sku_number', '')

        if ProductDetails.objects.filter(name=product_name, brand=brand_instance).exists() \
            or ProductDetails.objects.filter(sku_number=sku_number, brand=brand_instance).exists():
            return Response({'message': 'Product with the same name or SKU already exists under this brand.'}, status=status.HTTP_400_BAD_REQUEST)

        color_name = product_data.pop('color', '')  # Remove 'color' key from product_data
        
        try:
            color_instance = prod_col.objects.get(color=color_name)
        except prod_col.DoesNotExist:
            color_serializer = ProdColSerializer(data={'color': color_name})
            if color_serializer.is_valid():
                color_instance = color_serializer.save()
            else:
                return Response(color_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        sku_number = generate_unique_sku(product_data, color_instance)
        
        # Associate color instance with the product
        product_data['brand'] = brand_instance.id
        product_data['category_id'] = category_instance.id
        product_data['color_code'] = color_instance.id
        product_data['sku_number'] = sku_number
        
        product_serializer = ProductDetailsSerializer(data=product_data)
        
        if product_serializer.is_valid():
            product_instance = product_serializer.save()
            brand_name = Brand.objects.get(id=product_instance.brand_id).name
            product_data['brand_name'] = brand_name  # Add brand name to response data
            return Response({'message': 'Product created successfully.', 'brand_message': brand_message, 'product_data': product_data}, status=status.HTTP_201_CREATED)
        else:
            return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class ProductUpdateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]        
    @transaction.atomic
    @swagger_auto_schema(
        operation_summary="Update a product",
        operation_description="Update an existing product's details including brand, category, and color.",
        request_body=ProductDetailsSerializer,
        responses={200: openapi.Response("Product updated successfully", ProductDetailsSerializer)},
    )
    def put(self, request, prod_id):
        try:
            product_instance = ProductDetails.objects.get(prod_id=prod_id)
        except ProductDetails.DoesNotExist:
            return Response({'message': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.get('product', {})

        brand_data = data.pop('brand', {})
        if brand_data:
            brand_serializer = BrandSerializer(product_instance.brand, data=brand_data, partial=True)
            if brand_serializer.is_valid():
                brand_instance = brand_serializer.save()
            else:
                return Response(brand_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        color_data = data.pop('color', {})
        if color_data:
            color_serializer = ProdColSerializer(product_instance.color_code, data=color_data, partial=True)
            if color_serializer.is_valid():
                color_instance = color_serializer.save()
            else:
                return Response(color_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductDetailsSerializer(product_instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # @swagger_auto_schema(
    #     operation_summary="Delete all products",
    #     operation_description="Delete all products, categories, brands, and colors from the database.",
    # )
    # def delete(self, request):
    #         # Delete all products
    #         ProductDetails.objects.all().delete()
            
    #         # Delete all categories
    #         CategoryOfProducts.objects.all().delete()
            
    #         # Delete all brands
    #         Brand.objects.all().delete()
            
    #         # Delete all colors
    #         prod_col.objects.all().delete()
            
    #         return Response({"message": "All categories, brands, colors, and products deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
   

def generate_unique_sku(product_data, color_instance):
    ###
    # Generate unique alphanumeric SKU for the product color combination.
    # Example: ProductName-ColorCode-RandomNumber
    ###
    product_name = product_data.get('name', '').replace(" ", "-")
    color_code = color_instance.color.replace(" ", "-")
    
    # Generate a random alphanumeric string as part of the SKU
    random_string = ''.join([str(randint(0, 9)) for _ in range(4)])  # Change the range according to your preference
    
    # Combine the product name, color code, and random string to form the SKU
    sku_number = f"{product_name}-{color_code}-{random_string}"
    
    # Check if the generated SKU is unique
    while ProductDetails.objects.filter(sku_number=sku_number).exists():
        random_string = ''.join([str(randint(0, 9)) for _ in range(4)])
        sku_number = f"{product_name}-{color_code}-{random_string}"
    
    return sku_number


class DeleteProductView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    @swagger_auto_schema(
        operation_summary="Delete a product",
        operation_description="Delete a product from the database.",
        responses={204: "No content"},
    )
    def delete(self, request, prod_id):
        try:
            product_instance = ProductDetails.objects.filter(prod_id=prod_id).first()
            
            if not product_instance:
                return Response({"message": "Basic_Info with specified product ID does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete Basic_Info and associated PriceCost
            product_instance.delete()
            
            return Response({"message": "Basic_Info and associated PriceCost deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
        except (ProductDetails.DoesNotExist, Brand.DoesNotExist) as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)


class StoreDepotListAPIView(generics.GenericAPIView):

    queryset = StoreDepotModel.objects.all()
    serializer_class = StoreDepotSerializer

    @swagger_auto_schema(
        operation_summary="List and create stores",
        operation_description="List all stores or create a new store.",
        responses={200: "List of stores"},
    )
    def get(self, request):

        search_query = request.query_params.get('search', None)
        sort_by = request.query_params.get('sort_by', None)

        if search_query:
            stores = self.queryset.filter(
                Q(store_name__icontains=search_query) |
                Q(Country_code__icontains=search_query)
            )
        else:
            stores = self.queryset.all()

        # Sort stores if sort_by parameter is provided
        if sort_by:
            if sort_by.startswith('-'):
                stores = stores.order_by(sort_by[1:]).reverse()
            else:
                stores = stores.order_by(sort_by)

        serializer = self.serializer_class(stores, many=True)
        return Response(serializer.data)
    
class StoreDepotCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = StoreDepotSerializer
    @swagger_auto_schema(
        operation_summary="List and create stores",
        operation_description="List all stores or create a new store.",
        responses={200: StoreDepotSerializer(many=True)},
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Check if the contact number already exists
            contacts = serializer.validated_data.get('contacts')
            if StoreDepotModel.objects.filter(contacts=contacts).exists():
                raise ValidationError("A store with this contact number already exists.")

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StoreDepotRetrieveUpdateDestroyAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    # permission_classes = [ReadOnlyOrAdminPermission]
    queryset = StoreDepotModel.objects.all()
    serializer_class = StoreDepotSerializer

    def get_object(self, pk):
        try:
            return StoreDepotModel.objects.get(pk=pk)
        except StoreDepotModel.DoesNotExist:
            return Response({"message": "Error"})

    @swagger_auto_schema(
        operation_summary="Retrieve a store",
        operation_description="Fetch details of a store by its ID.",
        responses={200: StoreDepotSerializer},
    )
    def get(self, request, pk):
        """
        Retrieve details of a store by its ID.
        """
        store = self.get_object(pk)
        serializer = self.serializer_class(store)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Update a store",
        operation_description="Update details of a store by its ID.",
        request_body=StoreDepotSerializer,
        responses={200: StoreDepotSerializer, 400: "Bad request"},
    )
    def put(self, request, pk):
        """
        Update details of a store by its ID.
        """
        store = self.get_object(pk)
        serializer = self.serializer_class(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete a store",
        operation_description="Delete details of a store by its ID.",
        responses={204: "No content"},
    )
    def delete(self, request, pk):
        """
        Delete details of a store by its ID.
        """
        store = self.get_object(pk)
        store.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InventoryListAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = InventoryDEpartmentModel.objects.all()
    serializer_class = InventoryDEpartmentSerializer
    @swagger_auto_schema(
        operation_summary="List inventory items",
        operation_description="List all inventory items optionally filtered by search query and sorted by quantity.",
        manual_parameters=[
            openapi.Parameter(
                name="search_by",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter items by store name, product name, or quantity.",
                required=False,
            ),
            openapi.Parameter(
                name="sort_by",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Sort items by quantity. Use '-quantity' for descending order.",
                required=False,
            ),
        ],
        responses={200: InventoryDEpartmentSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', None)
        sort_by = request.query_params.get('sort_by', None)

        if search_query:
            queryset = self.queryset.filter(
                Q(store_id__store_name__icontains=search_query) |  
                Q(product_id__name__icontains=search_query) |    
                Q(quantity__icontains=search_query)               
            )
        else:
            queryset = self.queryset.all()

        if sort_by:
            if sort_by == 'quantity':
                queryset = queryset.order_by('-quantity')  # Sort by quantity in descending order
            elif sort_by == '-quantity':
                queryset = queryset.order_by('quantity')   # Sort by quantity in ascending order


        serialized_data = []
        for item in queryset:
            store_instance = item.store_id
            product_instance = item.product_id
            serialized_item = {
                'inventory_id': item.id,
                'store_name': store_instance.store_name,
                'product_name': product_instance.name,
                'quantity': item.quantity,
                'is_available': item.is_available
            }
            serialized_data.append(serialized_item)

        return Response(serialized_data)
    
class InventoryCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    @swagger_auto_schema(
        operation_summary="Create inventory item",
        operation_description="Create a new inventory item for a store with a specific product.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'store_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the store."),
                'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the product."),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description="Quantity of the product."),
            },
            required=['store_id', 'product_id', 'quantity']
        ),
        responses={
            201: InventoryDEpartmentSerializer(),
            400: "Bad Request: The product already exists in the store."
        },
    )
    def post(self, request, *args, **kwargs):
        store_id = request.data.get('store_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        print(store_id, product_id, quantity)

        store_instance = get_object_or_404(StoreDepotModel, pk=store_id)

        product_instance = get_object_or_404(ProductDetails, pk=product_id)

        if InventoryDEpartmentModel.objects.filter(store_id=store_instance, product_id=product_instance).exists():
            return Response({'error': f'The product "{product_instance.name}" already exists in the store.'}, status=status.HTTP_400_BAD_REQUEST)

        inventory_instance, created = InventoryDEpartmentModel.objects.get_or_create(
            store_id=store_instance,
            product_id=product_instance,
            defaults={'quantity': quantity}
        )

        inventory_instance.quantity = quantity
        inventory_instance.is_available = quantity > 0
        inventory_instance.save()

        store_name = store_instance.store_name
        product_name = product_instance.name

        response_data = {
            'inventory_id': inventory_instance.id,
            'store_id': store_id,
            'store_name': store_name,
            'product_id': product_id,
            'product_name': product_name,
            'quantity': quantity,
            'is_available': inventory_instance.is_available
        }

        return Response(response_data)

class InventoryUpdateAPIView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    queryset = InventoryDEpartmentModel.objects.all()
    serializer_class = InventoryDEpartmentSerializer

    def put(self, request, *args, **kwargs):
        inventory_id = kwargs.get('pk')
        quantity = request.data.get('quantity')

        inventory_instance = get_object_or_404(InventoryDEpartmentModel, pk=inventory_id)

        inventory_instance.quantity = quantity
        inventory_instance.is_available = quantity > 0
        inventory_instance.save()

        serializer = self.get_serializer(inventory_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailsImportExportView(generics.GenericAPIView):
    serializer_class = ProductDetailsSerializer

    def post(self, request):
        file = request.FILES.get('file')
        print("----->", file)
        if not file:
            return Response({'error': 'No file was uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith('.csv'):
            return Response({'error': 'File is not a CSV'}, status=status.HTTP_400_BAD_REQUEST)
        
        df = pd.read_csv(file)

        serializer = ProductDetailsSerializer(data=df)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        products = ProductDetails.objects.all()
        serializer = ProductDetailsSerializer(products, many=True)

        df = pd.DataFrame(serializer.data)

       
        category_names = {category.id: category.title for category in CategoryOfProducts.objects.all()}
        brand_names = {brand.id: brand.name for brand in Brand.objects.all()}
        color_names = {color.id: color.color for color in prod_col.objects.all()}

        
        df['category_name'] = df['category_id'].map(category_names)
        df['brand_name'] = df['brand'].map(brand_names)
        df['color_code'] = df['color_code'].map(color_names)

        
        df = df[['category_name', 'prod_id', 'brand_name', 'name', 'color_code', 'sku_number', 'description', 'review']]

        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_details.csv"'

        
        df.to_csv(path_or_buf=response, index=False)

        return response