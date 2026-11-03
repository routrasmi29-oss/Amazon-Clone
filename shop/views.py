from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncMonth
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from reportlab.pdfgen import canvas
from django.conf import settings

from decimal import Decimal
import json
import razorpay

from razorpay.errors import SignatureVerificationError

from .models import (
    Product,
    Cart,
    Order,
    OrderItem,
    Wishlist,
    Review,
    UserProfile,
    Coupon,
    ReturnRequest,
    RecentlyViewed,
)
from .notifications import send_order_email
client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)
def home(request):
    query = request.GET.get("q")
    category = request.GET.get("category")

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    if category and category != "All":
        products = products.filter(category__iexact=category)

    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=5
    )

    return render(request, "home.html", {
        "products": products,
        "query": query,
        "selected_category": category,
        "low_stock_products": low_stock_products,
    })
def live_search(request):

    query = request.GET.get("q", "").strip()

    categories = []
    products = []

    if query:

        # Search matching categories
        categories = list(
            Product.objects.filter(
                category__icontains=query
            )
            .values_list(
                "category",
                flat=True
            )
            .distinct()[:5]
        )

        # Search matching products
        products_queryset = Product.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query)
        )[:8]

        products = []

        for product in products_queryset:
            products.append({
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "image": product.image,
            })

    return JsonResponse({
        "categories": categories,
        "products": products
    })
@login_required
def product_detail(request,id):
    product=get_object_or_404(Product,id=id)

    reviews=Review.objects.filter(
        product=product
    ).order_by("-created_at")

    stats=reviews.aggregate(
        avg_rating=Avg("rating"),
        total_reviews=Count("id")
    )

    related_products=Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    )[:4]

    recently_viewed,created=RecentlyViewed.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        recently_viewed.viewed_at=timezone.now()
        recently_viewed.save()

    old_views=RecentlyViewed.objects.filter(
        user=request.user
    ).exclude(
        id=recently_viewed.id
    ).order_by("-viewed_at")

    old_view_ids=list(
        old_views.values_list("id",flat=True)[10:]
    )

    if old_view_ids:
        RecentlyViewed.objects.filter(
            id__in=old_view_ids
        ).delete()

    recently_viewed_products=Product.objects.filter(
        recentlyviewed__user=request.user
    ).exclude(
        id=product.id
    ).order_by(
        "-recentlyviewed__viewed_at"
    )[:10]

    return render(request,"product.html",{
        "product":product,
        "reviews":reviews,
        "avg_rating":stats["avg_rating"] or 0,
        "total_reviews":stats["total_reviews"],
        "related_products":related_products,
        "recently_viewed_products":recently_viewed_products,
    })
def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already exists")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(request,"Registration successful")

        return redirect("login")

    return render(request,"register.html")
def login_user(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful")
            return redirect("home")
        else:
            messages.error(request, "Invalid Username or Password")

    return render(request, "login.html")
def logout_user(request):
    logout(request)
    return redirect("home")

@login_required
def add_to_cart(request, id):

    product = get_object_or_404(Product, id=id)

    # Check product stock
    if product.stock <= 0:

        messages.error(
            request,
            f"{product.name} is currently out of stock."
        )

        return redirect("cart")


    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )


    # If product already exists in cart
    if not created:

        # Do not allow quantity more than available stock
        if cart_item.quantity >= product.stock:

            messages.error(
                request,
                f"Only {product.stock} item(s) available in stock."
            )

            return redirect("cart")


        cart_item.quantity += 1
        cart_item.save()


    return redirect("cart")
@login_required
def buy_now(request, id):

    product = get_object_or_404(Product, id=id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity = 1
        cart_item.save()

    return redirect("checkout")
@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = 0

    for item in cart_items:

        # Check if cart quantity is greater than available stock
        if item.quantity > item.product.stock:
            item.quantity = item.product.stock
            item.save()

        # If product is completely out of stock
        if item.product.stock == 0:
            item.quantity = 0
            item.save()

        item.subtotal = item.product.price * item.quantity
        total += item.subtotal

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total": total,
    })
@login_required
def increase_quantity(request, id):
    cart_item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    # Check available stock
    if cart_item.quantity < cart_item.product.stock:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart")
@login_required
def decrease_quantity(request, id):
    cart_item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect("cart")

@login_required
def remove_from_cart(request, id):
    cart_item = get_object_or_404(
        Cart,
        id=id,
        user=request.user
    )

    cart_item.delete()

    return redirect("cart")
@login_required
def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get("coupon", "").strip().upper()

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return redirect("checkout")

        if not coupon.is_valid():
            return redirect("checkout")

        cart_items = Cart.objects.filter(user=request.user)

        total = sum(
            item.product.price * item.quantity
            for item in cart_items
        )

        total = Decimal(str(total)).quantize(Decimal("0.01"))

        if total < coupon.minimum_amount:
            return redirect("checkout")

        if coupon.discount_type == "Percentage":
            discount = (total * coupon.discount) / Decimal("100")
        else:
            discount = coupon.discount

        discount = discount.quantize(Decimal("0.01"))

        if discount > total:
            discount = total

        final_total = total - discount
        final_total = final_total.quantize(Decimal("0.01"))

        request.session["coupon_code"] = coupon.code
        request.session["discount"] = str(discount)
        request.session["final_total"] = str(final_total)

        return redirect("checkout")

    return redirect("checkout")
@login_required
def checkout(request):
    cart_items=Cart.objects.filter(user=request.user).select_related("product")

    if not cart_items.exists():
        messages.error(request,"Your cart is empty.")
        return redirect("cart")

    for item in cart_items:
        if item.product.stock<=0:
            messages.error(request,f"{item.product.name} is currently out of stock.")
            return redirect("cart")

        if item.quantity>item.product.stock:
            messages.error(request,f"Only {item.product.stock} item(s) available for {item.product.name}.")
            return redirect("cart")

    total=Decimal("0.00")

    for item in cart_items:
        item.subtotal=item.product.price*item.quantity
        total+=item.subtotal

    discount=Decimal("0.00")
    coupon_code=request.session.get("coupon_code")

    if coupon_code:
        try:
            coupon=Coupon.objects.get(code=coupon_code)

            if coupon.is_valid() and total>=coupon.minimum_amount:

                if coupon.discount_type=="Percentage":
                    discount=(total*coupon.discount)/Decimal("100")
                else:
                    discount=coupon.discount

                if discount>total:
                    discount=total

            else:
                request.session.pop("coupon_code",None)

        except Coupon.DoesNotExist:
            request.session.pop("coupon_code",None)

    final_total=total-discount

    if final_total<0:
        final_total=Decimal("0.00")

    request.session["discount"]=str(discount)
    request.session["final_total"]=str(final_total)

    if request.method=="POST":
        fullname=request.POST.get("fullname","").strip()
        mobile=request.POST.get("mobile","").strip()
        address=request.POST.get("address","").strip()
        city=request.POST.get("city","").strip()
        state=request.POST.get("state","").strip()
        pincode=request.POST.get("pincode","").strip()
        payment=request.POST.get("payment","").strip()

        request.session["checkout_data"]={
            "full_name":fullname,
            "phone":mobile,
            "address":address,
            "city":city,
            "state":state,
            "pincode":pincode,
            "payment_method":payment,
        }

        if payment!="COD":
            amount=int(final_total*100)

            razorpay_order=client.order.create({
                "amount":amount,
                "currency":"INR",
                "payment_capture":1
            })

            request.session["razorpay_order_id"]=razorpay_order["id"]

            return render(request,"razorpay_checkout.html",{
                "cart_items":cart_items,
                "total":total,
                "discount":discount,
                "final_total":final_total,
                "fullname":fullname,
                "mobile":mobile,
                "address":address,
                "city":city,
                "state":state,
                "pincode":pincode,
                "payment":payment,
                "razorpay_order":razorpay_order,
                "key":settings.RAZORPAY_KEY_ID,
            })

        with transaction.atomic():

            for item in cart_items:
                item.product.refresh_from_db()

                if item.product.stock<item.quantity:
                    messages.error(request,f"Only {item.product.stock} item(s) available for {item.product.name}.")
                    return redirect("cart")

            order=Order.objects.create(
                user=request.user,
                full_name=fullname,
                phone=mobile,
                address=f"{address}, {city}, {state} - {pincode}",
                total_price=final_total,
                payment_method="COD",
                payment_status="Pending",
                order_status="Order Placed"
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

                item.product.stock-=item.quantity
                item.product.save()

            cart_items.delete()

        from django.core.mail import EmailMessage

        try:
            email=EmailMessage(
                subject="🎉 Order Confirmed - Amazon Clone",
                body=f"""Hello {request.user.username},

Your order has been placed successfully.

Order ID : {order.id}
Amount   : ₹{order.total_price}
Payment  : {order.payment_method}
Payment Status : {order.payment_status}
Order Status : {order.order_status}

Thank you for shopping with Amazon Clone.
Happy Shopping!""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email],
            )

            result=email.send()
            print("EMAIL SENT RESULT =",result)

        except Exception as e:
            print("EMAIL ERROR =",e)

        request.session["success_order_id"]=order.id
        request.session.pop("checkout_data",None)
        request.session.pop("razorpay_order_id",None)
        request.session.pop("discount",None)
        request.session.pop("final_total",None)
        request.session.pop("coupon_code",None)

        messages.success(request,"Order Placed Successfully")

        return redirect("order_success")

    return render(request,"checkout.html",{
        "cart_items":cart_items,
        "total":total,
        "discount":discount,
        "final_total":final_total,
        "coupon_code":coupon_code,
    })
@login_required
def order_success(request):
    order_id=request.session.pop("success_order_id",None)
    if not order_id:
        messages.error(request,"Order information not found.")
        return redirect("my_orders")
    order=get_object_or_404(Order,id=order_id,user=request.user)
    return render(request,"order_success.html",{"order":order})
@login_required
def my_orders(request):

    items = OrderItem.objects.filter(
        order__user=request.user
    ).order_by("-order__created_at")

    return render(request, "my_orders.html", {
        "items": items
    })

@login_required
def order_details(request, id):

    item = get_object_or_404(
        OrderItem,
        id=id,
        order__user=request.user
    )

    order = item.order

    return_request = ReturnRequest.objects.filter(
        order=order
    ).first()

    return render(
        request,
        "order_details.html",
        {
            "item": item,
            "order": order,
            "return_request": return_request,
        }
    )


@login_required
def return_order(request, id):

    item = get_object_or_404(
        OrderItem,
        id=id,
        order__user=request.user
    )

    order = item.order

    if order.order_status != "Delivered":
        messages.error(
            request,
            "Only delivered orders can be returned."
        )
        return redirect("order_details", id=item.id)

    existing_request = ReturnRequest.objects.filter(
        order=order
    ).first()

    if existing_request:
        messages.info(
            request,
            "Return request already submitted for this order."
        )
        return redirect("order_details", id=item.id)

    if request.method == "POST":

        reason = request.POST.get("reason")
        description = request.POST.get("description")

        if not reason:
            messages.error(
                request,
                "Please select a return reason."
            )
            return redirect("return_order", id=item.id)

        ReturnRequest.objects.create(
            order=order,
            reason=reason,
            description=description,
            refund_amount=order.total_price
        )

        messages.success(
            request,
            "Return request submitted successfully."
        )

        return redirect(
            "order_details",
            id=item.id
        )

    return render(
        request,
        "return_order.html",
        {
            "item": item,
            "order": order,
            "reasons": ReturnRequest.RETURN_REASONS,
        }
    )
@login_required
def add_to_wishlist(request, id):

    product = get_object_or_404(Product, id=id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect("home")


@login_required
def remove_from_wishlist(request, id):

    item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )

    item.delete()

    return redirect("wishlist")


@login_required
def wishlist(request):

    items = Wishlist.objects.filter(user=request.user)

    return render(request, "wishlist.html", {
        "items": items
    })

@login_required
def add_review(request, id):

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":

        rating = request.POST["rating"]
        comment = request.POST["comment"]

        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )

    return redirect("product_detail", id=id)

@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.mobile=request.POST.get("mobile")
        profile.address=request.POST.get("address")
        profile.city=request.POST.get("city")
        profile.state=request.POST.get("state")
        profile.pincode=request.POST.get("pincode")

        if request.FILES.get("profile_image"):
            profile.profile_image=request.FILES.get("profile_image")

        if request.FILES.get("camera_image"):
            profile.profile_image=request.FILES.get("camera_image")

        request.user.first_name=request.POST.get("fullname")
        request.user.email=request.POST.get("email")

        request.user.save()
        profile.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("profile")

    return render(request,"profile.html",{
        "profile":profile
    })
@login_required
@transaction.atomic
def payment_success(request):
    if request.method != "POST":
        return redirect("my_orders")
    razorpay_payment_id=request.POST.get("razorpay_payment_id")
    razorpay_order_id=request.POST.get("razorpay_order_id")
    razorpay_signature=request.POST.get("razorpay_signature")
    if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        messages.error(request,"Payment information is missing.")
        return redirect("payment_failed")
    order=Order.objects.filter(
        razorpay_order_id=razorpay_order_id,
        user=request.user
    ).first()
    if not order:
        messages.error(request,"Order not found for this payment.")
        return redirect("my_orders")
    order_item=OrderItem.objects.filter(order=order).first()
    if not order_item:
        messages.error(request,"Order item not found.")
        return redirect("my_orders")
    if order.payment_status=="Paid":
        messages.info(request,"Payment is already completed.")
        return redirect("order_details",id=order_item.id)
    params_dict={
        "razorpay_order_id":order.razorpay_order_id,
        "razorpay_payment_id":razorpay_payment_id,
        "razorpay_signature":razorpay_signature,
    }
    try:
        client.utility.verify_payment_signature(params_dict)
    except SignatureVerificationError:
        messages.error(request,"Payment Verification Failed.")
        return redirect("payment_failed")
    order.razorpay_payment_id=razorpay_payment_id
    order.razorpay_signature=razorpay_signature
    order.payment_status="Paid"
    order.save(update_fields=[
        "razorpay_payment_id",
        "razorpay_signature",
        "payment_status",
    ])
    from django.core.mail import send_mail
    try:
        send_mail(
            subject="🎉 Payment Successful - Amazon Clone",
            message=f"""
Hello {request.user.first_name or request.user.username},

Your payment was successful.

Order ID : {order.id}
Total Amount : ₹{order.total_price}
Payment Method : {order.payment_method}
Payment Status : {order.payment_status}

Your order has been confirmed successfully.

Thank you for shopping with Amazon Clone.

Happy Shopping!
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print("PAYMENT EMAIL ERROR =",e)
    request.session.pop("checkout_data",None)
    request.session.pop("razorpay_order_id",None)
    messages.success(request,"Payment Successful! Your order is now Paid.")
    return redirect("order_details",id=order_item.id)

@login_required
def payment_failed(request):
    messages.error(request,"Payment Failed")
    return render(request,"payment_failed.html")

@login_required
def cancel_order(request,order_id):
    order=get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )
    if order.order_status=="Order Placed":
        order_items=OrderItem.objects.filter(order=order)
        for item in order_items:
            product=item.product
            product.stock+=item.quantity
            product.save()
        order.order_status="Cancelled"
        order.save()
        messages.success(request,"Your order has been cancelled successfully.")
    else:
        messages.error(request,"This order cannot be cancelled.")
    return redirect("my_orders")
@login_required
def payment_failed(request):

    messages.error(request, "Payment Failed")

    return render(request, "payment_failed.html")

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if order.order_status == "Order Placed":

        order_items = OrderItem.objects.filter(order=order)

        for item in order_items:
            product = item.product
            product.stock += item.quantity
            product.save()

        order.order_status = "Cancelled"
        order.save()

        messages.success(
            request,
            "Your order has been cancelled successfully."
        )

    else:

        messages.error(
            request,
            "This order cannot be cancelled."
        )

    return redirect("my_orders")
@login_required
def download_invoice(request, id):

    item = get_object_or_404(
        OrderItem,
        id=id,
        order__user=request.user
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=Invoice_{item.order.id}.pdf'

    p = canvas.Canvas(response)

    y = 800

    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, y, "AMAZON CLONE")
    y -= 40

    p.setFont("Helvetica", 12)

    p.drawString(50, y, f"Invoice No : {item.order.id}")
    y -= 25

    p.drawString(50, y, f"Customer : {item.order.full_name}")
    y -= 25

    p.drawString(50, y, f"Phone : {item.order.phone}")
    y -= 25

    p.drawString(50, y, f"Address : {item.order.address}")
    y -= 25

    p.drawString(50, y, f"Product : {item.product.name}")
    y -= 25

    p.drawString(50, y, f"Quantity : {item.quantity}")
    y -= 25

    p.drawString(50, y, f"Price : ₹{item.price}")
    y -= 25

    p.drawString(50, y, f"Total : ₹{item.order.total_price}")
    y -= 25

    p.drawString(50, y, f"Payment Method : {item.order.payment_method}")
    y -= 25

    p.drawString(50, y, f"Payment Status : {item.order.payment_status}")
    y -= 25

    p.drawString(50, y, f"Order Status : {item.order.order_status}")
    y -= 25

    p.drawString(50, y, f"Date : {item.order.created_at.strftime('%d-%m-%Y %I:%M %p')}")
    y -= 40

    p.setFont("Helvetica-Bold", 14)
    p.drawString(120, y, "Thank You For Shopping With Us!")

    p.showPage()
    p.save()

    return response

@staff_member_required
def admin_dashboard(request):

    total_users = User.objects.count()

    total_orders = Order.objects.count()

    total_revenue = Order.objects.filter(
        payment_status="Paid"
    ).aggregate(
        total=Sum("total_price")
    )["total"] or 0

    pending_orders = Order.objects.filter(
        order_status="Order Placed"
    ).count()

    delivered_orders = Order.objects.filter(
        order_status="Delivered"
    ).count()

    cancelled_orders = Order.objects.filter(
        order_status="Cancelled"
    ).count()

    latest_orders = Order.objects.order_by("-created_at")[:5]

    # Monthly Sales
    monthly_sales = (
        Order.objects.filter(payment_status="Paid")
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total_price"))
        .order_by("month")
    )

    labels = []
    data = []

    for sale in monthly_sales:
        labels.append(sale["month"].strftime("%b"))
        data.append(float(sale["total"]))

    # Top Selling Products
    top_products = (
        OrderItem.objects.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    context = {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "latest_orders": latest_orders,

        "chart_labels": json.dumps(labels),
        "chart_data": json.dumps(data),

        "top_products": top_products,
    }

    return render(request, "admin_dashboard.html", context)
@staff_member_required
def admin_orders(request):
    orders=Order.objects.all().order_by("-created_at")

    search=request.GET.get("search","").strip()
    status=request.GET.get("status","").strip()

    if search:
        orders=orders.filter(
            Q(id__icontains=search) |
            Q(full_name__icontains=search) |
            Q(user__username__icontains=search)
        )

    if status:
        orders=orders.filter(order_status=status)

    total_orders=Order.objects.count()

    pending_orders=Order.objects.filter(
        order_status__in=[
            "Order Placed",
            "Confirmed",
            "Packed",
            "Shipped",
            "Out for Delivery"
        ]
    ).count()

    delivered_orders=Order.objects.filter(
        order_status="Delivered"
    ).count()

    cancelled_orders=Order.objects.filter(
        order_status="Cancelled"
    ).count()

    return render(request,"admin_orders.html",{
        "orders":orders,
        "statuses":Order.ORDER_STATUS,
        "search":search,
        "selected_status":status,
        "total_orders":total_orders,
        "pending_orders":pending_orders,
        "delivered_orders":delivered_orders,
        "cancelled_orders":cancelled_orders,
    })

@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("order_status")

        valid_statuses = [status[0] for status in Order.ORDER_STATUS]

        if new_status in valid_statuses:
            old_status = order.order_status

            order.order_status = new_status
            order.save()

            try:
                subject = f"Order #{order.id} - {new_status}"

                if new_status == "Confirmed":
                    message = f"""Hello {order.user.username},

Your order #{order.id} has been confirmed successfully.

Order ID : {order.id}
Amount : ₹{order.total_price}
Payment : {order.payment_method}
Payment Status : {order.payment_status}
Order Status : Confirmed

Thank you for shopping with Amazon Clone.
"""

                elif new_status == "Packed":
                    message = f"""Hello {order.user.username},

Your order #{order.id} has been packed successfully.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : Packed

Your order will be shipped soon.

Thank you for shopping with Amazon Clone.
"""

                elif new_status == "Shipped":
                    message = f"""Hello {order.user.username},

Good news! Your order #{order.id} has been shipped.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : Shipped

Your order is on the way.

Thank you for shopping with Amazon Clone.
"""

                elif new_status == "Out for Delivery":
                    message = f"""Hello {order.user.username},

Your order #{order.id} is out for delivery.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : Out for Delivery

Please keep your phone available for delivery.

Thank you for shopping with Amazon Clone.
"""

                elif new_status == "Delivered":
                    message = f"""Hello {order.user.username},

🎉 Your order #{order.id} has been delivered successfully.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : Delivered

Thank you for shopping with Amazon Clone.
We hope you enjoy your purchase!
"""

                elif new_status == "Cancelled":
                    message = f"""Hello {order.user.username},

Your order #{order.id} has been cancelled.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : Cancelled

If you have any questions, please contact our support team.

Thank you for shopping with Amazon Clone.
"""

                else:
                    message = f"""Hello {order.user.username},

Your order #{order.id} status has been updated.

Order ID : {order.id}
Amount : ₹{order.total_price}
Order Status : {new_status}

Thank you for shopping with Amazon Clone.
"""

                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[order.user.email],
                )

                email.send()

            except Exception:
                pass

            messages.success(
                request,
                f"Order #{order.id} status updated from {old_status} to {new_status}."
            )

    return redirect("admin_orders")
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return render(request, "admin_order_details.html", {
        "order": order,
        "statuses": Order.ORDER_STATUS,
    })
@staff_member_required
def admin_products(request):

    products = Product.objects.all().order_by("-id")

    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    if category:
        products = products.filter(category=category)

    return render(request, "admin_products.html", {
        "products": products,
        "categories": Product.CATEGORY_CHOICES,
        "search": search,
        "selected_category": category,
    })


@staff_member_required
def add_product(request):

    if request.method == "POST":

        name = request.POST.get("name")
        category = request.POST.get("category")
        price = request.POST.get("price")
        original_price = request.POST.get("original_price")
        discount = request.POST.get("discount")
        stock = request.POST.get("stock")
        image = request.POST.get("image")
        description = request.POST.get("description")

        Product.objects.create(
            name=name,
            category=category,
            price=price,
            original_price=original_price,
            discount=discount,
            stock=stock,
            image=image,
            description=description
        )

        messages.success(
            request,
            "Product added successfully."
        )

        return redirect("admin_products")

    return render(request, "add_product.html")


@staff_member_required
def edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.name = request.POST.get("name")
        product.category = request.POST.get("category")
        product.price = request.POST.get("price")
        product.original_price = request.POST.get("original_price")
        product.discount = request.POST.get("discount")
        product.stock = request.POST.get("stock")
        product.image = request.POST.get("image")
        product.description = request.POST.get("description")

        product.save()

        messages.success(
            request,
            "Product updated successfully."
        )

        return redirect("admin_products")

    return render(request, "edit_product.html", {
        "product": product,
        "categories": Product.CATEGORY_CHOICES,
    })


@staff_member_required
def delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.delete()

        messages.success(
            request,
            "Product deleted successfully."
        )

    return redirect("admin_products")
@login_required
def edit_product(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":

        product.name = request.POST.get("name")
        product.category = request.POST.get("category")
        product.price = request.POST.get("price")
        product.original_price = request.POST.get("original_price")
        product.discount = request.POST.get("discount")
        product.stock = request.POST.get("stock")
        product.image = request.POST.get("image")
        product.description = request.POST.get("description")

        product.save()

        messages.success(
            request,
            f"Product '{product.name}' updated successfully."
        )

        return redirect("admin_products")

    categories = Product.CATEGORY_CHOICES

    return render(
        request,
        "edit_product.html",
        {
            "product": product,
            "categories": categories,
        }
    )
@login_required
def pay_online(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    # Already paid
    if order.payment_status == "Paid":
        messages.info(
            request,
            "This order is already paid."
        )
        return redirect(
            "order_details",
            id=order.id
        )

    # Cancelled / delivered order
    if order.order_status in [
        "Cancelled",
        "Delivered"
    ]:
        messages.error(
            request,
            "Online payment is not available for this order."
        )
        return redirect(
            "order_details",
            id=order.id
        )

    amount = int(
        order.total_price * 100
    )

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # Save Razorpay Order ID
    order.razorpay_order_id = razorpay_order["id"]
    order.save(
        update_fields=["razorpay_order_id"]
    )

    return render(
        request,
        "pay_online.html",
        {
            "order": order,
            "razorpay_order": razorpay_order,
            "key": settings.RAZORPAY_KEY_ID,
        }
    )
@staff_member_required
def admin_return_requests(request):

    return_requests = ReturnRequest.objects.select_related(
        "order",
        "order__user"
    ).all().order_by("-created_at")

    status = request.GET.get("status", "").strip()

    if status:
        return_requests = return_requests.filter(status=status)

    return render(
        request,
        "admin_return_requests.html",
        {
            "return_requests": return_requests,
            "return_statuses": ReturnRequest.RETURN_STATUS,
            "selected_status": status,
        }
    )


@staff_member_required
def update_return_status(request, return_id):

    return_request = get_object_or_404(
        ReturnRequest,
        id=return_id
    )

    if request.method == "POST":

        new_status = request.POST.get("status")
        current_status = return_request.status

        # Allowed statuses
        valid_statuses = [
            status[0]
            for status in ReturnRequest.RETURN_STATUS
        ]

        if new_status not in valid_statuses:
            messages.error(
                request,
                "Invalid return status."
            )
            return redirect("admin_return_requests")

        # Status flow
        allowed_transitions = {
            "Requested": ["Approved", "Rejected"],
            "Approved": ["Picked Up"],
            "Picked Up": ["Refunded"],
            "Rejected": [],
            "Refunded": [],
        }

        if new_status not in allowed_transitions.get(
            current_status,
            []
        ):

            messages.error(
                request,
                f"Cannot change status from {current_status} to {new_status}."
            )

            return redirect("admin_return_requests")

        # Update return status
        return_request.status = new_status
        return_request.save()

        # ==============================
        # WHEN RETURN IS REFUNDED
        # ==============================
        if new_status == "Refunded":

            order = return_request.order

            # Update payment status
            order.payment_status = "Refunded"
            order.save()

            # Customer email
            customer_email = order.user.email

            if customer_email:

                subject = (
                    f"Payment Refunded - Order #{order.id}"
                )

                message = f"""
Hello {order.full_name},

Your return request for Order #{order.id} has been
processed successfully.

Your payment has been refunded.

Order ID: #{order.id}
Refund Amount: ₹{return_request.refund_amount}

The refunded amount will be credited according to
your payment provider's processing time.

Thank you for shopping with AmazonClone.

Regards,
AmazonClone Team
"""

                send_mail(
                    subject,
                    message,
                    None,
                    [customer_email],
                    fail_silently=False,
                )

            messages.success(
                request,
                f"Return #{return_request.id} refunded successfully."
            )

        else:

            messages.success(
                request,
                f"Return #{return_request.id} status updated to {new_status}."
            )

    return redirect("admin_return_requests")

@staff_member_required
def admin_return_detail(request, return_id):

    return_request = get_object_or_404(
        ReturnRequest,
        id=return_id
    )

    return render(
        request,
        "admin_return_detail.html",
        {
            "return_request": return_request,
            "return_statuses": ReturnRequest.RETURN_STATUS,
        }
    )