from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    context = {
        'title':'Home - Главная',
        'content':'Главная страница магазина - HOME'
    }
    return render(request,  'main/index.html', context)

def about(request):
    context = {
        'title': 'Home - О нас',
        'content': 'DANGER; pizda',
        'text_on_page': 'Starina, syebi nahuy... FUCK YOUU! '
    }
    return render(request, 'main/about.html', context)