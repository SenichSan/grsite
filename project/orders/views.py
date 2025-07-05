from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import FormView
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


class CreateOrderView(LoginRequiredMixin, FormView):
    template_name = 'orders/create_order.html'
    form_class = CreateOrderForm
    success_url = reverse_lazy('users:profile')

    def get_initial(self):
        initial = super().get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        return initial

    def form_valid(self, form):
        try:
            with transaction.atomic():
                if self.request.user.is_authenticated:
                    user = self.request.user
                    cart_items = Cart.objects.filter(user=user)

                    if cart_items.exists():
                        # Создать заказ
                        order = Order.objects.create(
                            user=user,
                            first_name=form.cleaned_data['first_name'],
                            last_name=form.cleaned_data['last_name'],
                            phone_number=form.cleaned_data['phone_number'],
                            email=form.cleaned_data['email'],
                            requires_delivery=form.cleaned_data['requires_delivery'],
                            delivery_address=form.cleaned_data['delivery_address'],
                            payment_on_get=form.cleaned_data['payment_on_get'],
                        )
                        # Создать заказанные товары
                        for cart_item in cart_items:
                            product = cart_item.product
                            name = cart_item.product.name
                            price = cart_item.product.sell_price()
                            quantity = cart_item.quantity

                            if product.quantity < quantity:
                                raise ValidationError(f'Недостаточное количество товара {name} на складе\
                                                           В наличии - {product.quantity}')

                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                name=name,
                                price=price,
                                quantity=quantity,
                            )
                            product.quantity -= quantity
                            product.save()

                        # Очистить корзину пользователя после создания заказа
                        cart_items.delete()

                        send_order_email_to_seller(order)
                        send_order_email_to_customer(order)

                        messages.success(self.request, 'Заказ оформлен!')
                        return redirect('user:profile')
        except ValidationError as e:
            messages.success(self.request, str(e))
            return redirect('orders:create_order')

    def form_invalid(self, form):
        messages.error(self.request, 'Заполните все обязательные поля!')
        return redirect('orders:create_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Оформление заказа'
        context['order'] = True
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