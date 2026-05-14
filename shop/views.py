from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Slider,  ProductCharacteristic
from .forms import OrderForm
from .utils import get_combined_bestsellers, get_top_products_by_category


def get_cart(request):
    """Получить или создать корзину для текущего пользователя/сессии"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        return None
    return cart


def get_common_context(request):
    """Общий контекст для всех страниц"""
    cart = get_cart(request)
    categories = Category.objects.all()

    cart_count = 0
    if cart:
        cart_count = cart.get_total_items()

    return {
        'cart_count': cart_count,
        'categories': categories,
    }
def index(request):
    """Главная страница"""
    latest_products = Product.objects.filter(in_stock=True).order_by('-created_at')[:8]
    bestsellers = get_combined_bestsellers(8)
    new_products = Product.objects.filter(is_new=True, in_stock=True)[:4]
    top_in_kirpich = get_top_products_by_category('kirpich', 4)
    top_in_cement = get_top_products_by_category('cement', 4)

    context = {
        'latest_products': latest_products,
        'bestsellers': bestsellers,
        'new_products': new_products,
        'top_in_kirpich': top_in_kirpich,
        'top_in_cement': top_in_cement,
    }
    context.update(get_common_context(request))
    return render(request, 'shop/index.html', context)


def catalog(request):
    """Каталог товаров с сортировкой и пагинацией"""
    products = Product.objects.filter(in_stock=True)

    # Сортировка
    sort_by = request.GET.get('sort', 'popular')

    if sort_by == 'popular':
        products = products.annotate(
            total_sold=Sum('orderitem__quantity')
        ).order_by('-total_sold', '-created_at')
    elif sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')

    # Фильтрация по поиску
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Фильтрация по категории
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    if min_price and min_price.isdigit():
        products = products.filter(price__gte=int(min_price))

    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=int(max_price))

    # Пагинация
    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'products': products_page,
        'search_query': search_query,
        'sort_by': sort_by,
        'paginator': paginator,
        'page_obj': products_page,
    }
    context.update(get_common_context(request))
    return render(request, 'shop/catalog.html', context)


def product_detail(request, slug):
    """Детальная страница товара"""
    product = get_object_or_404(Product, slug=slug, in_stock=True)
    sales_count = product.get_sales_count()
    characteristics = ProductCharacteristic.objects.filter(product=product).select_related('characteristic')
    related_products = Product.objects.filter(
        category=product.category,
        in_stock=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'sales_count': sales_count,
        'characteristics': characteristics,
        'related_products': related_products,
    }
    context.update(get_common_context(request))
    return render(request, 'shop/product_detail.html', context)


@login_required
def add_to_cart(request):
    """Добавление в корзину"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Для добавления товаров в корзину необходимо авторизоваться!')
        return redirect('login')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)

        if not cart:
            cart = Cart.objects.create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, f'{product.name} добавлен в корзину!')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'cart_count': cart.get_total_items()})

        return redirect('cart')


@login_required
def cart_view(request):
    """Корзина"""
    cart = get_cart(request)
    if not cart:
        cart = Cart.objects.create(user=request.user)

    cart_items = cart.items.all()

    context = {
        'cart_items': cart_items,
        'cart_total': cart.get_total_price(),
    }
    context.update(get_common_context(request))
    return render(request, 'shop/cart.html', context)


@login_required
def update_cart(request):
    """Обновление корзины"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 0))
        cart_item = get_object_or_404(CartItem, id=item_id)

        if cart_item.cart.user != request.user:
            return HttpResponseForbidden('У вас нет прав на это действие')

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

        cart = get_cart(request)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'item_total': float(cart_item.product.price * quantity) if quantity > 0 else 0,
                'cart_total': float(cart.get_total_price()),
                'cart_count': cart.get_total_items()
            })

        return redirect('cart')


@login_required
def checkout(request):
    """Оформление заказа"""
    cart = get_cart(request)
    if not cart:
        cart = Cart.objects.create(user=request.user)

    cart_items = cart.items.all()

    if not cart_items:
        messages.warning(request, 'Ваша корзина пуста!')
        return redirect('catalog')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = cart.get_total_price()
            order.user = request.user
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            cart.items.all().delete()
            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('order_success', order_id=order.id)
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = OrderForm(initial=initial_data)

    context = {
        'cart_items': cart_items,
        'cart_total': cart.get_total_price(),
        'form': form,
    }
    context.update(get_common_context(request))
    return render(request, 'shop/checkout.html', context)


@login_required
def order_success(request, order_id):
    """Страница успешного заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}
    context.update(get_common_context(request))
    return render(request, 'shop/order_success.html', context)


def about(request):
    """Страница о компании"""
    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/about.html', context)


def delivery(request):
    """Страница доставки"""
    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/delivery.html', context)


def contacts(request):
    """Страница контактов"""
    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/contacts.html', context)


def register(request):
    """Регистрация"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if password != password2:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'shop/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует!')
            return render(request, 'shop/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует!')
            return render(request, 'shop/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        auth_login(request, user)
        messages.success(request, f'Добро пожаловать, {username}!')
        return redirect('index')

    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/register.html', context)


def user_login(request):
    """Вход"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f'С возвращением, {username}!')
            return redirect('index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')

    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/login.html', context)


@login_required
def user_logout(request):
    """Выход"""
    auth_logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('index')


@login_required
def profile(request):
    """Личный кабинет"""
    context = {}
    context.update(get_common_context(request))
    return render(request, 'shop/profile.html', context)


@login_required
def order_history(request):
    """История заказов"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {'orders': orders}
    context.update(get_common_context(request))
    return render(request, 'shop/order_history.html', context)


