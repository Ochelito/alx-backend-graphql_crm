from django.db import models
from django.core.validators import RegexValidator, MinValueValidator

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^(\+\d{1,3})?[\d\s-]{7,15}$',
                message="Phone number must be valid format (+1234567890 or 123-456-7890)"
            )
        ]
    )

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    products = models.ManyToManyField(Product, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate total_amount from product prices
        self.total_amount = sum([p.price for p in self.products.all()])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"
