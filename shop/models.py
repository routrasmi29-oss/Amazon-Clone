from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Shoes", "Shoes"),
        ("Fashion", "Fashion"),
        ("Mobiles", "Mobiles"),
        ("Laptops", "Laptops"),
        ("Headphones", "Headphones"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="Shoes"
    )
    color = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=10)
    image = models.URLField()
    description = models.TextField()

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Order(models.Model):
    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded"),
    ]

    ORDER_STATUS = [
        ("Order Placed", "Order Placed"),
        ("Confirmed", "Confirmed"),
        ("Packed", "Packed"),
        ("Shipped", "Shipped"),
        ("Out for Delivery", "Out for Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(max_length=50)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    order_status = models.CharField(
        max_length=30,
        choices=ORDER_STATUS,
        default="Order Placed"
    )

    razorpay_order_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    razorpay_payment_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    razorpay_signature = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    mobile = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True
    )

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    DISCOUNT_TYPE = [
        ("Flat", "Flat"),
        ("Percentage", "Percentage"),
    ]

    code = models.CharField(max_length=50, unique=True)

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE,
        default="Flat"
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    minimum_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    expiry_date = models.DateField()
    active = models.BooleanField(default=True)

    def is_valid(self):
        return (
            self.active
            and self.expiry_date >= timezone.now().date()
        )

    def __str__(self):
        return self.code


class ReturnRequest(models.Model):
    RETURN_STATUS = [
        ("Requested", "Requested"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Picked Up", "Picked Up"),
        ("Refunded", "Refunded"),
    ]

    RETURN_REASONS = [
        ("Wrong Product", "Wrong Product"),
        ("Damaged Product", "Damaged Product"),
        ("Product Not Needed", "Product Not Needed"),
        ("Size Issue", "Size Issue"),
        ("Quality Issue", "Quality Issue"),
        ("Other", "Other"),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="return_request"
    )

    reason = models.CharField(
        max_length=50,
        choices=RETURN_REASONS
    )

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS,
        default="Requested"
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return #{self.id} - Order #{self.order.id}"


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"