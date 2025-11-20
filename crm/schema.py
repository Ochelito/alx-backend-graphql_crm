import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.db import transaction
from django.core.exceptions import ValidationError

# ObjectTypes
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

# Mutations
class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")
        customer = Customer(name=name, email=email, phone=phone)
        customer.full_clean()  # validation for phone
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.List(
            graphene.InputObjectType(
                name="CustomerInput",
                fields={
                    "name": graphene.String(required=True),
                    "email": graphene.String(required=True),
                    "phone": graphene.String()
                }
            )
        )

    def mutate(self, info, input):
        created = []
        errors = []
        for c in input:
            try:
                customer = Customer(name=c["name"], email=c["email"], phone=c.get("phone"))
                customer.full_clean()
                customer.save()
                created.append(customer)
            except Exception as e:
                errors.append(f"{c.get('email')}: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(default_value=0)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("Stock cannot be negative")
        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)

    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = Product.objects.filter(id__in=product_ids)
        if not products.exists():
            raise Exception("No valid products selected")

        order = Order(customer=customer)
        order.save()  # save first to create m2m relation
        order.products.set(products)
        order.total_amount = sum([p.price for p in products])
        order.save()
        return CreateOrder(order=order)

# Combine mutations
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# Basic query for testing
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
