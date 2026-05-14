from django.contrib import admin
from .models import Category, Product, Slider, Characteristic, ProductCharacteristic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'id')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'category', 'price', 'is_bestseller', 'in_stock', 'is_new')
    list_filter = ('category', 'is_bestseller', 'is_new', 'in_stock')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_bestseller', 'is_new', 'in_stock')


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'preview')
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'subtitle')

    fieldsets = (
        ('Изображение', {
            'fields': ('image', 'image_url')
        }),
        ('Текст слайда', {
            'fields': ('title', 'subtitle', 'description')
        }),
        ('Кнопка', {
            'fields': ('button_text', 'button_link')
        }),
        ('Настройки', {
            'fields': ('order', 'is_active')
        }),
    )

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 50px;"/>'
        elif obj.image_url:
            return f'<img src="{obj.image_url}" style="height: 50px;"/>'
        return '-'

    preview.allow_tags = True
    preview.short_description = 'Превью'


@admin.register(Characteristic)
class CharacteristicAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit')
    search_fields = ('name',)
    list_editable = ('unit',)


@admin.register(ProductCharacteristic)
class ProductCharacteristicAdmin(admin.ModelAdmin):
    list_display = ('product', 'characteristic', 'value')
    list_filter = ('product__category', 'characteristic')
    search_fields = ('product__name', 'characteristic__name', 'value')
