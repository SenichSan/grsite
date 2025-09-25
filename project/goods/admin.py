from django.contrib import admin
from .models import Categories, Products, ProductImage



@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "sort_order"]
    list_editable = ["sort_order"]
    search_fields = ["name", "short_description", "description"]
    fields = [
        "name",
        "slug",
        "short_description",
        "description",
        "image",
        "seo_image",
        "sort_order",
    ]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "species", "quantity", "price", "discount", "gift_enabled"]
    list_editable = ["discount", "gift_enabled", "species"]
    search_fields = ["name", "short_description", "description"]
    list_filter = ["category", "species", "discount", "quantity"]
    fields = [
        "name",
        "category",
        "slug",
        "short_description",
        "description",
        "image",
        "card_image",
        ("price", "discount"),
        "quantity",
        "is_bestseller",
        "gift_enabled",
        "species",
    ]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text")
