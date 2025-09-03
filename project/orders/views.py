from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import FormView, TemplateView
from carts.models import Cart
from orders.forms import CreateOrderForm
from orders.models import Order, OrderItem
import requests
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET

from orders.utils import send_order_email_to_seller, send_order_email_to_customer

# для nova poshta api
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

def get_user_carts(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user)
    else:
        return Cart.objects.filter(session_key=request.session.session_key)


class CreateOrderView(FormView):
    template_name = 'orders/create_order.html'
    form_class = CreateOrderForm
    success_url = reverse_lazy('main:index')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial['first_name'] = self.request.user.first_name
            initial['last_name'] = self.request.user.last_name
            initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        try:
            with transaction.atomic():
                cart_items = get_user_carts(self.request)
                
                if cart_items.exists():
                    form_data = form.cleaned_data
                    delivery_address = self.request.POST.get('delivery_address', '').strip()
                    comment = self.request.POST.get('comment', '').strip()

                    # Предварительная проверка наличия товаров на складе
                    insufficient = []
                    for cart_item in cart_items:
                        product = cart_item.product
                        if cart_item.quantity > product.quantity:
                            insufficient.append(
                                f"{product.name}: доступно {product.quantity}, в корзине {cart_item.quantity}"
                            )
                    if insufficient:
                        messages.error(
                            self.request,
                            "Недостаточно товара на складе:\n" + "\n".join(insufficient)
                        )
                        return redirect('orders:create_order')

                    # Создаем заказ
                    # Нормализуем способ доставки для сохранения читаемой метки
                    raw_delivery = self.request.POST.get('delivery_method', '') or ''
                    delivery_label = 'Нова Пошта' if raw_delivery in ('courier', 'nova', 'nova_poshta') else (raw_delivery or 'Нова Пошта')

                    order = Order.objects.create(
                        user=self.request.user if self.request.user.is_authenticated else None,
                        first_name=form_data['first_name'],
                        last_name=form_data['last_name'],
                        phone_number=form_data['phone_number'],
                        email=form_data['email'],
                        requires_delivery=delivery_label,
                        delivery_address=delivery_address,
                        payment_on_get=form_data.get('payment_on_get', False),
                    )

                    # Создаем позиции заказа
                    for cart_item in cart_items:
                        product = cart_item.product
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            name=product.name,
                            price=product.sell_price(),
                            quantity=cart_item.quantity,
                        )
                        
                        # Обновляем количество товара на складе (после предварительной проверки)
                        product.quantity = product.quantity - cart_item.quantity
                        product.save(update_fields=["quantity"])

                    # Очищаем корзину
                    cart_items.delete()

                    # Отправляем уведомления
                    send_order_email_to_seller(order, comment)
                    if order.email:
                        send_order_email_to_customer(order)

                    # Разрешаем просмотр страницы успеха для этого заказа (гостям и на случай разлогина)
                    allowed = self.request.session.get('allowed_orders') or []
                    if order.id not in allowed:
                        allowed.append(order.id)
                        self.request.session['allowed_orders'] = allowed
                        self.request.session.modified = True

                    messages.success(self.request, 'Заказ успешно оформлен!')
                    return redirect('orders:order_success', order_id=order.id)
                else:
                    messages.error(self.request, 'Ваша корзина пуста')
                    return redirect('orders:create_order')

        except Exception as e:
            messages.error(self.request, f'Ошибка при оформлении заказа: {str(e)}')
            return redirect('orders:create_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Оформление заказа'
        context['order'] = True
        return context


class OrderSuccessView(TemplateView):
    template_name = 'orders/order_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)

        # Контроль доступа
        user = self.request.user
        if user.is_authenticated:
            # Разрешаем только владельцу заказа; если заказ гостевой (user=None) — проверяем по сессии
            if order.user_id:
                if order.user_id != user.id:
                    raise Http404()
            else:
                allowed = self.request.session.get('allowed_orders', [])
                if order.id not in allowed:
                    raise Http404()
        else:
            # Гость: только если заказ разрешен для текущей сессии
            allowed = self.request.session.get('allowed_orders', [])
            if order.id not in allowed:
                raise Http404()
        items = OrderItem.objects.filter(order=order).select_related('product')
        items_data = [
            {
                'obj': it,
                'name': it.name,
                'price': it.price,
                'quantity': it.quantity,
                'subtotal': it.price * it.quantity,
            }
            for it in items
        ]
        total_qty = sum(d['quantity'] for d in items_data)
        total_sum = sum(d['subtotal'] for d in items_data)

        context['order'] = order
        context['items'] = items
        context['items_data'] = items_data
        context['total_qty'] = total_qty
        context['total_sum'] = total_sum
        return context


# nova poshta поиск отделений
API_KEY = '65ef3beeda1b3897b0e3e4d66b759a93'


def search_city(request):
    q = request.GET.get('q', '')[:100]
    if len(q) < 2:
        return JsonResponse([], safe=False)
    payload = {
        "apiKey": API_KEY,
        "modelName": "AddressGeneral",
        "calledMethod": "searchSettlements",
        "methodProperties": {
            "CityName": q,
            "Limit": 10,
            "Page": 1
        }
    }
    try:
        resp = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=7)
        resp.raise_for_status()
        data = resp.json()
        block = (data.get('data') or [])
        addresses = block[0].get('Addresses') if block and isinstance(block[0], dict) else []
        items = []
        for c in addresses or []:
            label = c.get("Present") or ""
            ref = c.get("Ref") or c.get("DeliveryCity") or ""
            if label and ref:
                items.append({"label": label, "ref": ref})
        return JsonResponse(items, safe=False)
    except Exception:
        # Fail gracefully to avoid 500 on UI
        return JsonResponse([], safe=False)


@require_GET
def get_warehouses(request):
    settlement_ref = request.GET.get("settlement_ref")
    if not settlement_ref:
        return JsonResponse({"success": False, "warehouses": []})

    payload = {
        "apiKey": API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "SettlementRef": settlement_ref
        }
    }
    resp = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=5).json()
    if resp.get("success"):
        whs = [w["Description"] for w in resp["data"]]
        return JsonResponse({"success": True, "warehouses": whs})
    return JsonResponse({"success": False, "warehouses": []})

def get_warehouse_description(ref):
    payload = {
        "apiKey": API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "Ref": ref
        }
    }
    try:
        res = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=5).json()
        if res.get("success") and res["data"]:
            return res["data"][0]["Description"]
    except Exception:
        pass
    return ref  # fallback: просто вернуть ref, если что-то пошло не так
