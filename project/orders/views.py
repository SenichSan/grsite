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
from django.http import JsonResponse
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
                    city_name = self.request.POST.get('city_name', '').strip()
                    warehouse_ref = self.request.POST.get('warehouse_ref', '').strip()
                    warehouse_desc = get_warehouse_description(warehouse_ref)
                    
                    # Создаем заказ
                    order = Order.objects.create(
                        user=self.request.user if self.request.user.is_authenticated else None,
                        first_name=form_data['first_name'],
                        last_name=form_data['last_name'],
                        phone_number=form_data['phone_number'],
                        email=form_data['email'],
                        delivery_address=f"{city_name}, {warehouse_desc}",
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
                        
                        # Обновляем количество товара на складе
                        product.quantity -= cart_item.quantity
                        product.save()

                    # Очищаем корзину
                    cart_items.delete()

                    # Отправляем уведомления
                    send_order_email_to_seller(order)
                    if order.email:
                        send_order_email_to_customer(order)

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
        context['order'] = get_object_or_404(Order, id=order_id)
        return context


# nova poshta поиск отделений
API_KEY = '65ef3beeda1b3897b0e3e4d66b759a93'


def search_city(request):
    q = request.GET.get('q', '')[:100]
    if len(q) < 2:
        return JsonResponse([], safe=False)
    payload = {
        "apiKey": API_KEY,
        "modelName": "Address",
        "calledMethod": "searchSettlements",
        "methodProperties": {
            "CityName": q,
            "Limit": 10
        }
    }
    resp = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload, timeout=5).json()
    addresses = resp.get('data', [])
    if addresses and addresses[0].get('Addresses'):
        cities = addresses[0]['Addresses']
        return JsonResponse(
            [{"label": c["Present"], "ref": c["Ref"]} for c in cities],
            safe=False
        )
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
