from django.db import models
from django.urls import reverse
from tinymce.models import HTMLField


class Categories(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    short_description = models.CharField(max_length=300, blank=True, null=True, verbose_name='Краткое описание')
    image = models.ImageField(upload_to='categories_images', blank=True, null=True, verbose_name='Изображение')
    sort_order = models.PositiveIntegerField(default=100, db_index=True, verbose_name='Порядок')

    class Meta:
        db_table = 'category'
        verbose_name = 'Категорию'
        verbose_name_plural = 'Категории'
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.name


class Products(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    short_description = models.CharField(max_length=300, blank=True, null=True, verbose_name='Краткое описание')
    description = HTMLField(blank=True, null=True, verbose_name='Описание')
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    price = models.DecimalField(default=0.00, max_digits=7, decimal_places=2, verbose_name='Цена')
    discount = models.DecimalField(default=0.00, max_digits=4, decimal_places=2, verbose_name='Скидка в %')
    quantity = models.PositiveIntegerField(default=0, verbose_name='Количество')
    category = models.ForeignKey(to=Categories, on_delete=models.CASCADE, verbose_name='Категория')
    is_bestseller = models.BooleanField(default=False, verbose_name='Лидер продаж')



    class Meta:
        db_table = 'product'
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ("id",)

    def __str__(self):
        return f'{self.name} Количество - {self.quantity}'

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"product_slug": self.slug})
    

    def display_id(self):
        return f"{self.id:05}"


    def sell_price(self):
        if self.discount:
            return round(self.price - self.price*self.discount/100, 2)
        
        return self.price

    def discount_price(self):
        if self.discount:
            return round(self.price * self.discount/100, 2)

        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Изображение продукта'
        verbose_name_plural = 'Изображения продукта'

    def __str__(self):
        return f'{self.product.name} – #{self.pk}'