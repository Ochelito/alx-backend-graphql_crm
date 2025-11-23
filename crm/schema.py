import re
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from crm.models import Product, Customer, Order
import django_filters

# ============================================================
# FILTERS
# ============================================================

class CustomerFilter(django_filters.FilterSet):
    name_icontains = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email_icontains = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    created_at_gte = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    phone_pattern = django_filters.CharFilter(method="filter_phone_pattern")
    order_by = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('email', 'email'),
            ('created_at', 'created_at'),
        )
    )

    class Meta:
        model = Customer
        fields = []

    def filter_phone_pattern(self, queryset, name, value):
        return queryset.filter(phone__startswith=value)


class ProductFilter(django_filters.FilterSet):
    name_icontains = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price_gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock_gte = django_filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock_lte = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")
    order_by = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('price', 'price'),
            ('stock', 'stock'),
        )
    )

    class Meta:
        model = Product
        fields = []


class OrderFilter(django_filters.FilterSet):
    total_amount_gte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount_lte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    order_date_gte = django_filters.DateFilter(field_name="order_date", lookup_expr="gte")
    order_date_lte = django_filters.DateFilter(field_name="order_date", lookup_expr="lte")
    customer_name = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = django_filters.CharFilter(method="filter_product_name")
    product_id = django_filters.NumberFilter(method="filter_product_id")
    order_by = django_filters.OrderingFilter(
        fields=(
            ('total_amount', 'total_amount'),
            ('order_date', 'order_date'),
        )
    )

    class Meta:
        model = Order
        fields = []

    def filter_product_name(self, queryset, name, value):
        return queryset.filter(products__name__icontains=value)

    def filter_product_id(self, queryset, name, value):
        return queryset.filter(products__id=value)


# ============================================================
# OBJECT TYPES (GraphQL Nodes)
# ============================================================

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# ============================================================
# INPUT TYPES
# ============================================================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


# ============================================================
# VALIDATION
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
# MUTATIONS
# ============================================================

class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerNode)
    message = graphene.String()
    error = graphene.String()

    class Arguments:
        input = CustomerInput(required=True)

    def mutate(self, info, input):
        error = validate_email_and_phone(input.email, input.phone)
        if error:
            return CreateCustomer(error=error)
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(error="Email already exists")
        customer = Customer(name=input.name, email=input.email, phone=input.phone or "")
        customer.full_clean()
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    customers = graphene.List(CustomerNode)
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
            customer = Customer(name=c.name, email=c.email, phone=c.phone or "")
            try:
                customer.full_clean()
                customer.save()
                created.append(customer)
            except Exception as e:
                errors.append(f"[{idx}] {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductNode)
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
        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderNode)
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
        order = Order(customer=customer, total_amount=total_amount)
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)


# ============================================================
# ROOT MUTATION
# ============================================================

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductNode)
    message = graphene.String()

    def mutate(self, info):
        # Find products with stock < 10
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_products = []

        for product in low_stock_products:
            product.stock += 10  # restock
            product.save()
            updated_products.append(product)

        return UpdateLowStockProducts(
            updated_products=updated_products,
            message=f"{len(updated_products)} products restocked successfully"
        )


# Add to root mutation
Mutation.update_low_stock_products = UpdateLowStockProducts.Field()

# ============================================================
# ROOT QUERY
# ============================================================

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

    all_customers = DjangoFilterConnectionField(CustomerNode)
    all_products = DjangoFilterConnectionField(ProductNode)
    all_orders = DjangoFilterConnectionField(OrderNode)


# ============================================================
# SCHEMA
# ============================================================

schema = graphene.Schema(query=Query, mutation=Mutation)
