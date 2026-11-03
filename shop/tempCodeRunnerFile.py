@login_required
def checkout(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = 0

    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
        total += item.subtotal

    discount = request.session.get("discount", 0)
    final_total = float(total) - float(discount)

    if final_total < 0:
        final_total = 0

    if request.method == "POST":

        fullname = request.POST["fullname"]
        mobile = request.POST["mobile"]
        address = request.POST["address"]
        city = request.POST["city"]
        state = request.POST["state"]
        pincode = request.POST["pincode"]
        payment = request.POST["payment"]

        request.session["checkout_data"] = {
            "full_name": fullname,
            "phone": mobile,
            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,
            "payment_method": payment,
        }

        # Razorpay Payment
        if payment != "COD":

            amount = int(float(final_total) * 100)

            razorpay_order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1
            })

            request.session["razorpay_order_id"] = razorpay_order["id"]

            return render(request, "razorpay_checkout.html", {
                "cart_items": cart_items,
                "total": total,
                "fullname": fullname,
                "mobile": mobile,
                "address": address,
                "city": city,
                "state": state,
                "pincode": pincode,
                "payment": payment,
                "razorpay_order": razorpay_order,
                "key": settings.RAZORPAY_KEY_ID,
            })

        # Stock Check
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(request, f"{item.product.name} is out of stock.")
                return redirect("cart")

        # Create Order
        order = Order.objects.create(
            user=request.user,
            full_name=fullname,
            phone=mobile,
            address=f"{address}, {city}, {state} - {pincode}",
            total_price=final_total,
            payment_method=payment,
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

            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()

        print("=" * 60)
        print("Logged in user :", request.user.username)
        print("User email     :", request.user.email)
        print("=" * 60)

        from django.core.mail import EmailMessage

        try:
            email = EmailMessage(
                subject="🎉 Order Confirmed - Amazon Clone",
                body=f"""
Hello {request.user.username},

Your order has been placed successfully.

Order ID : {order.id}
Amount   : ₹{order.total_price}
Payment  : {order.payment_method}

Thank you for shopping with Amazon Clone.

Happy Shopping!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email],
            )

            result = email.send()

            print("EMAIL SENT RESULT =", result)

        except Exception as e:
            print("EMAIL ERROR =", e)

        request.session.pop("checkout_data", None)
        request.session.pop("razorpay_order_id", None)

        messages.success(request, "Order Placed Successfully")

        return redirect("order_success")

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "total": total,
        "discount": discount,
        "final_total": final_total,
        "coupon_code": request.session.get("coupon_code"),
    })