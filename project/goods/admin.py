from django.contrib import admin
from .models import Categories, Products, ProductImage



@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "sort_order"]
    list_editable = ["sort_order"]
    search_fields = ["name", "short_description"]
    fields = [
        "name",
        "slug",
        "short_description",
        "image",
        "sort_order",
    ]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "quantity", "price", "discount"]
    list_editable = ["discount"]
    search_fields = ["name", "short_description", "description"]
    list_filter = ["discount", "quantity", "category"]
    fields = [
        "name",
        "category",
        "slug",
        "short_description",
        "description",
        "image",
        ("price", "discount"),
        "quantity",
        "is_bestseller",
    ]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "alt_text")
