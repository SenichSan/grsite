from django.http import HttpResponse
from django.shortcuts import render
from unicodedata import category

from goods.models import Categories


def index(request):

    categories = Categories.objects.all()

    context = {
        'title':'Home - Главная',
        'content':'Главная страница магазина - HOME',
        'categories': categories
    }
    return render(request,  'main/index.html', context)

def about(request):
    context = {
        'title': 'Home - О нас',
        'content': 'DANGER; pizda',
        'text_on_page': 'Starina, syebi nahuy... FUCK YOUU! '
    }
    return render(request, 'main/about.html', context)