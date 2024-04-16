# utils.py

import random
from .models import ProductDetails
def generate_unique_sku(product_data, color_instance):
    ###
    # Generate unique alphanumeric SKU for the product color combination.
    # Example: ProductName-ColorCode-RandomNumber
    ###
    product_name = product_data.get('name', '').replace(" ", "-")
    color_code = color_instance.color.replace(" ", "-")
    
    # Generate a random alphanumeric string as part of the SKU
    random_string = ''.join([str(random.randint(0, 9)) for _ in range(4)])  # Change the range according to your preference
    
    # Combine the product name, color code, and random string to form the SKU
    sku_number = f"{product_name}-{color_code}-{random_string}"
    
    # Check if the generated SKU is unique
    while ProductDetails.objects.filter(sku_number=sku_number).exists():
        random_string = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        sku_number = f"{product_name}-{color_code}-{random_string}"
    
    return sku_number
