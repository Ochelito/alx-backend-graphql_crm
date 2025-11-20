import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql_crm.settings")
django.setup()

from crm.models import Customer, Product

def seed_customers():
    Customer.objects.bulk_create([
        Customer(name="Alice", email="alice@example.com", phone="+1234567890"),
        Customer(name="Bob", email="bob@example.com", phone="123-456-7890"),
        Customer(name="Carol", email="carol@example.com")
    ])

def seed_products():
    Product.objects.bulk_create([
        Product(name="Laptop", price=999.99, stock=10),
        Product(name="Mouse", price=19.99, stock=50),
        Product(name="Keyboard", price=49.99, stock=30)
    ])

if __name__ == "__main__":
    seed_customers()
    seed_products()
    print("Database seeded successfully!")
