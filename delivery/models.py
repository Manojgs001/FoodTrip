from django.db import models

# Create your models here.
class Customer(models.Model):
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=255)   # long enough for hashed passwords
    email    = models.CharField(max_length=100)
    mobile   = models.CharField(max_length=15)
    address  = models.CharField(max_length=200)

class Restaurant(models.Model):
    name    = models.CharField(max_length=50)
    picture = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    cuisine = models.CharField(max_length=200)
    rating  = models.FloatField()

    def get_picture_url(self):
        """Returns correct URL for legacy URLs, base64 data URIs, and new uploaded images."""
        if not self.picture:
            return ''
        val = str(self.picture)
        if val.startswith(('http://', 'https://', '/static/', '/media/', 'data:')):
            return val          # old-style URL or base64 — use directly
        return self.picture.url # new upload — serve via /media/

class Item(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='items')
    name        = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    price       = models.FloatField()
    vegeterian  = models.BooleanField(default=False)
    picture     = models.ImageField(upload_to='menu_items/', blank=True, null=True)

    def get_picture_url(self):
        """Returns correct URL for legacy URLs, base64 data URIs, and new uploaded images."""
        if not self.picture:
            return ''
        val = str(self.picture)
        if val.startswith(('http://', 'https://', '/static/', '/media/', 'data:')):
            return val
        return self.picture.url

# Cart uses a plain M2M (kept intact to avoid migration issues).
# CartItem tracks per-item quantities separately.
class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart')
    items    = models.ManyToManyField('Item', related_name='carts', blank=True)

    def total_price(self):
        total = 0
        for ci in self.cart_items.all():
            total += ci.item.price * ci.quantity
        return total

    def item_count(self):
        return sum(ci.quantity for ci in self.cart_items.all())

class CartItem(models.Model):
    """Tracks quantity of each item in a cart."""
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    item     = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='cart_entries')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'item')

    def subtotal(self):
        return self.item.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending',          'Pending'),
        ('Paid',             'Paid'),
        ('Preparing',        'Preparing'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered',        'Delivered'),
        ('Failed',           'Failed'),
    )
    customer           = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    total_price        = models.FloatField()
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    razorpay_order_id  = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer.username} - {self.status}"

class OrderItem(models.Model):
    order              = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item               = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    price_at_purchase  = models.FloatField()
    quantity           = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item.name if self.item else 'Deleted Item'} x{self.quantity} (Order {self.order.id})"

class Rating(models.Model):
    customer   = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ratings')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='ratings')
    stars      = models.PositiveSmallIntegerField()   # 1-5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'restaurant')   # one rating per customer per restaurant

    def __str__(self):
        return f"{self.customer.username} rated {self.restaurant.name}: {self.stars}★"