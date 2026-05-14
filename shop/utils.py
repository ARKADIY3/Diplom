from django.db.models import Sum
from .models import Product


def get_bestsellers(limit=8):
    """Получить самые продаваемые товары на основе заказов"""
    bestsellers = Product.objects.filter(
        in_stock=True,
        orderitem__isnull=False
    ).annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:limit]

    return bestsellers


def get_manual_bestsellers(limit=8):
    """Получить товары, отмеченные как хиты вручную"""
    return Product.objects.filter(is_bestseller=True, in_stock=True)[:limit]


def get_combined_bestsellers(limit=8):
    """Комбинирует автоматические и ручные хиты продаж"""
    auto_bestsellers = list(get_bestsellers(limit))
    auto_ids = [p.id for p in auto_bestsellers]
    manual_bestsellers = Product.objects.filter(
        is_bestseller=True,
        in_stock=True
    ).exclude(id__in=auto_ids)[:limit - len(auto_bestsellers)]

    combined = auto_bestsellers + list(manual_bestsellers)
    return combined[:limit]


def get_top_products_by_category(category_slug=None, limit=5):
    """Получить топ товаров по категории"""
    products = Product.objects.filter(in_stock=True)

    if category_slug:
        products = products.filter(category__slug=category_slug)

    return products.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:limit]