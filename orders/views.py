from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from cart.models import Cart, CartItem
from .models import Order, OrderItem


@login_required
def checkout(request):

    cart, created = Cart.objects.get_or_create(user=request.user)

    items = CartItem.objects.filter(cart=cart)

    total = 0

    for item in items:
        total += item.subtotal()

    context = {
        "items": items,
        "total": total,
    }

    return render(request, "orders/checkout.html", context)


@login_required
def place_order(request):

    if request.method == "POST":

        phone = request.POST["phone"]

        # Phone Number Validation
        if not phone.isdigit() or len(phone) != 10:
            messages.error(
                request,
                "Phone number must contain exactly 10 digits."
            )
            return redirect("checkout")

        cart = get_object_or_404(Cart, user=request.user)

        items = CartItem.objects.filter(cart=cart)

        total = sum(item.subtotal() for item in items)

        order = Order.objects.create(
            user=request.user,
            full_name=request.POST["full_name"],
            phone=phone,
            email=request.POST["email"],
            address=request.POST["address"],
            total_amount=total,
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )

        items.delete()

        return redirect("payment", order_id=order.id)

    return redirect("checkout")


@login_required
def payment(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if request.method == "POST":

        payment_method = request.POST.get("payment_method")
        payment_screenshot = request.FILES.get("payment_screenshot")

        if not payment_method:
            messages.error(
                request,
                "Please select a payment method."
            )
            return redirect("payment", order_id=order.id)

        if not payment_screenshot:
            messages.error(
                request,
                "Please upload your payment screenshot."
            )
            return redirect("payment", order_id=order.id)

        order.payment_method = payment_method
        order.payment_screenshot = payment_screenshot
        order.payment_status = "Pending Verification"

        order.save()

        return redirect(
            "payment_success",
            order_id=order.id
        )

    return render(
        request,
        "orders/payment.html",
        {
            "order": order
        }
    )


@login_required
def payment_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    if order.stock_reduced:
        messages.info(request, "Stock has already been reduced for this order.")

    order_items = OrderItem.objects.filter(order=order)

    for item in order_items:
        product = item.product
        print("stock before:", product.stock)
        print("order quantity:", item.quantity)
        if product.stock >= item.quantity:
            product.stock -= item.quantity
            product.save()

    order.stock_reduced = True
    order.save()

    return redirect(
        "order_success",
        order_id=order.id
    )


@login_required
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
            "payment_screenshot": order.payment_screenshot,
        }
    )

@login_required
def invoice(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    order_items = OrderItem.objects.filter(
        order=order
    )

    return render(
        request,
        "orders/invoice.html",
        {
            "order": order,
            "order_items": order_items,
        }
    )


@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-id")

    return render(
        request,
        "orders/my_orders.html",
        {
            "orders": orders
        }
    )