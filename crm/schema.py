import re
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from .models import Customer, Product, Order


# ============================================================
#   OBJECT TYPES
# ============================================================

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ============================================================
#   INPUT TYPES
# ============================================================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


# ============================================================
#   VALIDATION FUNCTION
# ============================================================

def validate_email_and_phone(email, phone=None):
    try:
        validate_email(email)
    except ValidationError:
        return "Invalid email format"

    if phone:
        pattern = r'^(\+?\d{10,15}|(\d{3}-\d{3}-\d{4}))$'
        if not re.match(pattern, phone):
            return "Invalid phone number format"
    return None


# ============================================================
#   MUTATIONS
# ============================================================

class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    error = graphene.String()

    class Arguments:
        input = CustomerInput(required=True)

    def mutate(self, info, input):
        # Validate email/phone
        error = validate_email_and_phone(input.email, input.phone)
        if error:
            return CreateCustomer(error=error)

        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(error="Email already exists")

        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone or ""
        )
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    @transaction.atomic
    def mutate(self, info, input):
        created = []
        errors = []

        for idx, c in enumerate(input):
            error = validate_email_and_phone(c.email, c.phone)
            if error:
                errors.append(f"[{idx}] {error}")
                continue
            if Customer.objects.filter(email=c.email).exists():
                errors.append(f"[{idx}] Email already exists: {c.email}")
                continue
            customer = Customer.objects.create(
                name=c.name,
                email=c.email,
                phone=c.phone or ""
            )
            created.append(customer)

        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    error = graphene.String()

    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(default_value=0)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            return CreateProduct(error="Price must be positive")
        if stock < 0:
            return CreateProduct(error="Stock cannot be negative")

        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    error = graphene.String()

    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    @transaction.atomic
    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(error="Invalid customer ID")

        if not product_ids:
            return CreateOrder(error="At least one product is required")

        products = []
        total_amount = 0
        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
                total_amount += product.price
            except Product.DoesNotExist:
                return CreateOrder(error=f"Invalid product ID: {pid}")

        order = Order.objects.create(customer=customer, total_amount=total_amount)
        order.products.set(products)

        return CreateOrder(order=order)


# ============================================================
#   ROOT MUTATION
# ============================================================

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# ============================================================
#   ROOT QUERY
# ============================================================

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()


# ============================================================
#   SCHEMA
# ============================================================

schema = graphene.Schema(query=Query, mutation=Mutation)
