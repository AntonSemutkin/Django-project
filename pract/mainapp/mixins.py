from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View

from .models import Category, Cart, Client, MinimallyInvasiveUrology, Disinfectants, Glassware


class CategoryDetailMixin(SingleObjectMixin):
    """
    Mixin for displaying categories
    """
    CATEGORY_SLUG_TO_CLOTHES_MODEL = {
        'minimallyinvasiveurology': MinimallyInvasiveUrology,
        'glassware': Glassware,
        'disinfectants': Disinfectants
    }

    def get_context_data(self, **kwargs):
        if isinstance(self.get_object(), Category):
            model = self.CATEGORY_SLUG_TO_CLOTHES_MODEL[self.get_object().slug]
            context = super().get_context_data(**kwargs)
            context['categories'] = Category.objects.get_categories_for_nav()
            context['category_product'] = model.objects.all()
            return context
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.get_categories_for_nav()
        return context


class CartMixin(View):
    """
    Mixin for displaying cart
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            client = Client.objects.filter(user=request.user).first()
            if not client:
                client = Client.objects.create(user=request.user)
            cart = Cart.objects.filter(owner=client, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(owner=client)
        else:
            cart = Cart.objects.filter(anon_user=True).first()
            if not cart:
                cart = Cart.objects.create(anon_user=True)
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)


class AuthenticatedSuperuserMixin(object):
    """
    mixin will check if the user is superuser
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.add_message(request, messages.INFO, 'Недостаточно прав!')
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)


class AuthenticatedUserMixin(object):
    """
    mixin will check if the user is logged in
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.add_message(request, messages.INFO, 'Сначала войдите в аккаунт!')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)