from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Category, Product, Wishlist, Cart, Order, OrderItem,
    Review, WholesaleRequest
)

def index(request):
    categories = Category.objects.all()
    return render(request, 'catalog/index.html', {'categories': categories})

def category_detail(request, cat_slug):
    category = get_object_or_404(Category, slug=cat_slug)
    products = category.products.all()
    return render(request, 'catalog/category.html', {
        'category': category,
        'products': products,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by('-created_at')
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'reviews': reviews,
    })

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'catalog/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f"Товар '{product.name}' добавлен в избранное")
    return redirect('catalog:wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"Товар '{product.name}' удалён из избранного")
    return redirect('catalog:wishlist')

def get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        return Cart.objects.filter(session_key=session_key)

def cart_view(request):
    cart_items = get_cart(request)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'catalog/cart.html', {'cart_items': cart_items, 'total': total})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_item, created = Cart.objects.get_or_create(session_key=session_key, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"Товар '{product.name}' добавлен в корзину")
    return redirect('catalog:cart')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id)
    if request.user.is_authenticated and cart_item.user == request.user:
        cart_item.delete()
    elif cart_item.session_key == request.session.session_key:
        cart_item.delete()
    messages.success(request, "Товар удалён из корзины")
    return redirect('catalog:cart')

def update_cart_quantity(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=item_id)
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('catalog:cart')

@login_required
def checkout(request):
    cart_items = get_cart(request)
    if not cart_items:
        messages.warning(request, "Корзина пуста")
        return redirect('catalog:cart')
    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        company = request.POST.get('company', '')
        city = request.POST.get('city', '')
        street = request.POST.get('street', '')
        house = request.POST.get('house', '')
        comment = request.POST.get('comment', '')
        if not address or not phone:
            messages.error(request, "Заполните обязательные поля")
            return render(request, 'catalog/checkout.html', {'cart_items': cart_items})
        total = sum(item.total_price() for item in cart_items)
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_price=total,
                address=address,
                phone=phone,
                company=company,
                city=city,
                street=street,
                house=house,
                comment=comment
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.get_final_price()
                )
            cart_items.delete()
        messages.success(request, f"Заказ №{order.id} оформлен!")
        return redirect('catalog:order_confirmation', order_id=order.id)
    return render(request, 'catalog/checkout.html', {'cart_items': cart_items})

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'catalog/order_confirmation.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'catalog/order_history.html', {'orders': orders})

def sale_products(request):
    products = Product.objects.filter(is_on_sale=True)
    return render(request, 'catalog/sale.html', {'products': products})

def bestsellers(request):
    products = Product.objects.filter(is_bestseller=True)
    return render(request, 'catalog/bestsellers.html', {'products': products})

def favorite_tricot(request):
    products = Product.objects.filter(is_bestseller=True)[:10]
    return render(request, 'catalog/favorite_tricot.html', {'products': products})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        if rating and text:
            Review.objects.create(
                product=product,
                user=request.user,
                name=request.user.username,
                rating=int(rating),
                text=text
            )
            messages.success(request, 'Спасибо за ваш отзыв!')
        else:
            messages.error(request, 'Заполните все поля')
    return redirect('catalog:product_detail', product_id=product_id)

def wholesale_request_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        comment = request.POST.get('comment', '')
        consent = request.POST.get('consent') == 'on'
        if name and phone and consent:
            WholesaleRequest.objects.create(
                name=name,
                phone=phone,
                comment=comment,
                consent=consent
            )
            messages.success(request, "Заявка отправлена!")
            return redirect('catalog:wholesale')
        else:
            messages.error(request, "Заполните все обязательные поля")
    return render(request, 'catalog/wholesale.html')

def feedback(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message')
        if name and email and message:
            Feedback.objects.create(name=name, email=email, phone=phone, message=message)
            messages.success(request, "Ваша заявка отправлена!")
            return redirect('catalog:feedback')
        else:
            messages.error(request, "Заполните все обязательные поля")
    return render(request, 'catalog/feedback.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})