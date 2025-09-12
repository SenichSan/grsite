from django.http import Http404
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Products, Categories
from .utils import q_search
from django.core.cache import cache


class CatalogView(ListView):
    model = Products
    template_name = "goods/catalog.html"
    context_object_name = "goods"
    paginate_by = 10
    allow_empty = False
    slug_url_kwarg = "category_slug"

    def get_queryset(self):
        # Base queryset with prefetch of related images to avoid N+1 in templates
        base_qs = Products.objects.all().prefetch_related('images')

        category_slug = self.kwargs.get(self.slug_url_kwarg)
        on_sale = self.request.GET.get("on_sale")
        order_by = self.request.GET.get("order_by")
        query = self.request.GET.get("q")

        # Text search (ensure prefetch is preserved if q_search returns a queryset)
        if query:
            goods = q_search(query)
            try:
                goods = goods.prefetch_related('images')
            except AttributeError:
                goods = base_qs.none()
        else:
            if not category_slug or category_slug == "all":
                goods = base_qs
            else:
                goods = base_qs.filter(category__slug=category_slug)
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
        # Cache categories list to avoid repeated DB hits
        categories = cache.get('categories_ordered')
        if categories is None:
            categories = Categories.objects.order_by('sort_order', 'name')
            cache.set('categories_ordered', categories, 1800)  # 30 minutes
        context["categories"] = categories
        context['current_category'] = self.kwargs.get(self.slug_url_kwarg, 'all')
        # Provide selected category object (for image + description presentation)
        current_slug = context['current_category']
        context['current_category_obj'] = None
        if current_slug:
            context['current_category_obj'] = Categories.objects.filter(slug=current_slug).first()
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

        # Похожие товары: из той же категории, исключая текущий товар
        related_products = (
            Products.objects
            .filter(category=product.category)
            .exclude(pk=product.pk)
            .order_by('?')[:10]
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
