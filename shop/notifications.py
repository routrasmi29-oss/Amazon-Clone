from django.conf import settings
from django.core.mail import EmailMessage


def send_order_email(order,event):
    subject=""
    message=""

    if event=="order_confirmed":
        subject="🎉 Order Confirmed - Amazon Clone"
        message=f"""Hello {order.user.username},

Your order has been confirmed successfully.

Order ID : #{order.id}
Amount   : ₹{order.total_price}
Payment  : {order.payment_method}
Payment Status : {order.payment_status}
Order Status : {order.order_status}

Thank you for shopping with Amazon Clone.
Happy Shopping!"""

    elif event=="payment_success":
        subject="✅ Payment Successful - Amazon Clone"
        message=f"""Hello {order.user.username},

Your payment has been received successfully.

Order ID : #{order.id}
Amount   : ₹{order.total_price}
Payment : {order.payment_method}
Payment Status : {order.payment_status}

Thank you for shopping with Amazon Clone."""

    elif event=="order_shipped":
        subject="🚚 Order Shipped - Amazon Clone"
        message=f"""Hello {order.user.username},

Your order has been shipped.

Order ID : #{order.id}
Amount   : ₹{order.total_price}
Order Status : {order.order_status}

Your order is on the way.
Thank you for shopping with Amazon Clone."""

    elif event=="order_delivered":
        subject="📦 Order Delivered - Amazon Clone"
        message=f"""Hello {order.user.username},

Your order has been delivered successfully.

Order ID : #{order.id}
Amount   : ₹{order.total_price}

Thank you for shopping with Amazon Clone."""

    elif event=="order_cancelled":
        subject="❌ Order Cancelled - Amazon Clone"
        message=f"""Hello {order.user.username},

Your order has been cancelled.

Order ID : #{order.id}
Amount   : ₹{order.total_price}
Order Status : {order.order_status}

If a refund is applicable, it will be processed according to the payment method.

Thank you for shopping with Amazon Clone."""

    elif event=="refund_initiated":
        subject="💰 Refund Initiated - Amazon Clone"
        message=f"""Hello {order.user.username},

Your refund has been initiated.

Order ID : #{order.id}
Refund Amount : ₹{order.total_price}

You will receive the refund according to the payment provider's processing time."""

    elif event=="refund_completed":
        subject="💵 Refund Completed - Amazon Clone"
        message=f"""Hello {order.user.username},

Your refund has been completed successfully.

Order ID : #{order.id}
Refund Amount : ₹{order.total_price}
Payment Status : {order.payment_status}

Thank you for shopping with Amazon Clone."""

    else:
        return False

    if not order.user.email:
        print("EMAIL ERROR = Customer email not available")
        return False

    try:
        email=EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )

        result=email.send()

        print("EMAIL SENT RESULT =",result)

        return result==1

    except Exception as e:
        print("EMAIL ERROR =",e)
        return False