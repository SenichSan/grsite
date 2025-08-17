# carts/views.py
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction

from .models import Cart
from .utils import get_user_carts

from goods.models import Products


def _owner_filter(request):
    """Возвращаем фильтр для запросов: по user или session_key"""
    if request.user.is_authenticated:
        return {'user': request.user}
    if not request.session.session_key:
        request.session.create()
    return {'session_key': request.session.session_key}


class CartAddView(View):
    """
    Ожидает POST: product_id, quantity (опционально)
    Если запись уже есть -> увеличивает quantity.
    Возвращает JSON с cart_items_html, total_quantity, total_sum, message.
    """
    def post(self, request):
        product_id = request.POST.get('product_id') or request.POST.get('id')
        try:
            qty = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1

        if not product_id:
            return JsonResponse({'error': 'product_id is required'}, status=400)

        product = get_object_or_404(Products, id=product_id)
        owner = _owner_filter(request)

        with transaction.atomic():
            cart_qs = Cart.objects.filter(product=product, **owner)
            cart_item = cart_qs.first()
            if cart_item:
                # увеличиваем
                cart_item.quantity = cart_item.quantity + qty
                cart_item.save(update_fields=['quantity'])
            else:
                cart_item = Cart.objects.create(product=product, quantity=qty, **owner)

        # рендерим обновлённый список корзины
        carts = get_user_carts(request)
        # вычисляем суммарные значения
        total_quantity = sum(item.quantity for item in carts)
        total_sum = round(sum(float(item.product.sell_price()) * item.quantity for item in carts), 2)
        # рендерим HTML с уже посчитанными итогами
        html = render_to_string(
            'carts/includes/included_cart.html',
            {'carts': carts, 'total_quantity': total_quantity, 'total_sum': total_sum},
            request=request,
        )

        return JsonResponse({
            'message': 'Товар добавлен в корзину',
            'cart_items_html': html,
            'total_quantity': total_quantity,
            'total_sum': total_sum,
        })


class CartChangeView(View):
    """
    Меняет количество одной строки корзины.
    Ожидает POST: cart_id, action (increment/decrement) или quantity (число).
    Возвращает JSON с обновлённым cart_items_html, total_quantity, total_sum
    """
    def post(self, request):
        cart_id = request.POST.get('cart_id')
        if not cart_id:
            return JsonResponse({'error': 'cart_id required'}, status=400)

        # фильтруем по владельцу — чтобы нельзя было трогать чужие строки
        owner = _owner_filter(request)
        cart_item = get_object_or_404(Cart, id=cart_id, **owner)

        action = request.POST.get('action')
        qty = request.POST.get('quantity')
        try:
            if action == 'increment':
                cart_item.quantity += 1
                cart_item.save(update_fields=['quantity'])
            elif action == 'decrement':
                cart_item.quantity -= 1
                if cart_item.quantity <= 0:
                    cart_item.delete()
                else:
                    cart_item.save(update_fields=['quantity'])
            elif qty is not None:
                new_qty = max(0, int(qty))
                if new_qty == 0:
                    cart_item.delete()
                else:
                    cart_item.quantity = new_qty
                    cart_item.save(update_fields=['quantity'])
            else:
                return JsonResponse({'error': 'action or quantity required'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        carts = get_user_carts(request)
        total_quantity = sum(item.quantity for item in carts)
        total_sum = round(sum(float(item.product.sell_price()) * item.quantity for item in carts), 2)
        html = render_to_string(
            'carts/includes/included_cart.html',
            {'carts': carts, 'total_quantity': total_quantity, 'total_sum': total_sum},
            request=request,
        )

        return JsonResponse({
            'message': 'Количество обновлено',
            'cart_items_html': html,
            'total_quantity': total_quantity,
            'total_sum': total_sum,
        })


class CartRemoveView(View):
    """
    Удаляет строку корзины. Ожидает POST: cart_id.
    """
    def post(self, request):
        cart_id = request.POST.get('cart_id')
        if not cart_id:
            return JsonResponse({'error': 'cart_id required'}, status=400)
        owner = _owner_filter(request)
        cart_item = get_object_or_404(Cart, id=cart_id, **owner)
        cart_item.delete()

        carts = get_user_carts(request)
        total_quantity = sum(item.quantity for item in carts)
        total_sum = round(sum(float(item.product.sell_price()) * item.quantity for item in carts), 2)
        html = render_to_string(
            'carts/includes/included_cart.html',
            {'carts': carts, 'total_quantity': total_quantity, 'total_sum': total_sum},
            request=request,
        )

        return JsonResponse({
            'message': 'Товар удалён',
            'cart_items_html': html,
            'total_quantity': total_quantity,
            'total_sum': total_sum,
        })


# Optional: CartDetailView для GET /cart/view/
class CartDetailView(View):
    def get(self, request):
        carts = get_user_carts(request)
        total_quantity = sum(item.quantity for item in carts)
        total_sum = round(sum(float(item.product.sell_price()) * item.quantity for item in carts), 2)
        html = render_to_string(
            'carts/includes/included_cart.html',
            {'carts': carts, 'total_quantity': total_quantity, 'total_sum': total_sum},
            request=request,
        )
        return JsonResponse({'cart_items_html': html, 'total_quantity': total_quantity, 'total_sum': total_sum})
