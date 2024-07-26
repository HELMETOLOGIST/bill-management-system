from django.db import models
import uuid

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=100)
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=10)
    number = models.IntegerField()
    order_id = models.CharField(max_length=8, primary_key=True, unique=True, editable=False)
    date = models.DateField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()
        super().save(*args, **kwargs)

    def generate_order_id(self):
        return str(uuid.uuid4().hex)[:8]

    def __str__(self):
        return self.name
