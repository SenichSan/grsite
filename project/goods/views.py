from django.http import Http404
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Products, Categories
from .utils import q_search


class CatalogView(ListView):
    model = Products
    template_name = "goods/catalog.html"
    context_object_name = "goods"
    paginate_by = 12
    allow_empty = False
    slug_url_kwarg = "category_slug"

    def get_queryset(self):
        qs = Products.objects.prefetch_related('images').all()
        category_slug = self.kwargs.get(self.slug_url_kwarg)
        on_sale = self.request.GET.get("on_sale")
        order_by = self.request.GET.get("order_by")
        query = self.request.GET.get("q")

        if category_slug == "all" or not category_slug:
            goods = super().get_queryset()
        elif query:
            goods = q_search(query)
        else:
            goods = super().get_queryset().filter(category__slug=category_slug)
            if not goods.exists():
                raise Http404()

        if on_sale:
            goods = goods.filter(discount__gt=0)

        if order_by and order_by != "default":
            goods = goods.order_by(order_by)

        return goods

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Home - Каталог"
        context["slug_url"] = self.kwargs.get(self.slug_url_kwarg)
        context["categories"] = Categories.objects.order_by('sort_order', 'name')
        context['current_category'] = self.kwargs.get(self.slug_url_kwarg, 'all')
        return context


    def render_to_response(self, context, **response_kwargs):
        # Если AJAX — возвращаем только partial с товарами
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, "goods/_products_list.html", context)
        return super().render_to_response(context, **response_kwargs)


class ProductView(DetailView):
    model = Products
    template_name = "goods/product.html"
    context_object_name = "product"
    slug_url_kwarg = "product_slug"

    def get_queryset(self):
        return super().get_queryset().prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Подбираем похожие товары из той же категории, исключая текущий
        related_products = (
            Products.objects
                    .filter(category=product.category)
                    .exclude(pk=product.pk)
                    .order_by('?')
                    [:10]
        )

        context.update({
            'title': product.name,
            'related_products': related_products,
        })
        return context


class CategoriesView(ListView):
    model = Categories
    template_name = 'goods/categories.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Все категории"
        context["categories"] = Categories.objects.order_by('sort_order', 'name')
        return context
