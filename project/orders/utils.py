# orders/utils.py

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail, EmailMultiAlternatives


# Отправляет письмо продавцу о новом заказе
def send_order_email_to_seller(order):
    items = order.orderitem_set.all()

    if not items.exists():
        return  # Не отправляем письмо, если товаров нет (на всякий случай)

    item_lines = '\n'.join([
        f"{item.name} — Кол-во: {item.quantity}, Цена: {item.price * item.quantity}"
        for item in items
    ])
    order_price = sum(item.price * item.quantity for item in items)
    message = (
        f"Новый заказ №{order.id}\n\n"
        f"Товары:\n{item_lines}\n\n"
        f"Общая стоимость заказа: {order_price}\n\n"
        f"Адрес доставки:\n{order.requires_delivery}\n\n"
        f"Имя клиента: {order.first_name.upper()}\n"
        f"Фамилия клиента: {order.last_name.upper()}\n"
        f"Телефон: {order.phone_number}\n"
        f"Email: {order.user.email if order.user else '—'}"
    )

    send_mail(
        subject=f"Новый заказ №{order.id}",
        message=message,
        from_email='shroomer0ua@gmail.com',
        recipient_list=['shroomer0ua@gmail.com'],
        fail_silently=False
    )

def send_order_email_to_customer(order):
    items = order.orderitem_set.all()

    if not items.exists():
        return  # Не отправляем письмо, если товаров нет (на всякий случай)

    item_lines = '\n'.join([
        f"{item.name} — Кол-во: {item.quantity}, Цена: {item.price * item.quantity}"
        for item in items
    ])
    order_price = sum(item.price * item.quantity for item in items)

    message = (
        f"Новый заказ №{order.id}\n\n"
        f"Товары:\n{item_lines}\n\n"
        f"Общая стоимость заказа: {order_price}\n\n"
        f"Адрес доставки:\n{order.delivery_address or 'Самовывоз'}\n\n"
        f"Имя клиента: {order.first_name.upper()}\n"
        f"Фамилия клиента: {order.last_name.upper()}\n"
        f"Телефон: {order.phone_number}\n"
        f"Email: {order.email}"
    )

    html_message = render_to_string('order_confirmation_email.html', {
        'order': order,
        'items': items,
        'total_price': order_price,
    })

    # Отправка письма с двумя форматами
    email = EmailMultiAlternatives(
        subject=f"Ваш заказ №{order.id}",
        body=message,
        from_email='shroomer0ua@gmail.com',
        to=[order.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send()