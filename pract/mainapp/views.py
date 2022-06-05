from django.db import transaction
from django.shortcuts import render
from django.views.generic import DetailView, View, UpdateView, CreateView
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.urls.base import reverse_lazy

from .models import MinimallyInvasiveUrology, Disinfectants, Glassware, Category, LatestProducts, CartProduct, Client, Order, User
from .mixins import CartMixin, CategoryDetailMixin, AuthenticatedSuperuserMixin, AuthenticatedUserMixin
from .forms import OrderForm, LoginForm, RegistrationForm, GlasswareForm, DisinfectantsForm, MinimallyInvasiveUrologyForm
from .utils import recalc_cart


class BaseView(CartMixin, View):

    def get(self, request):
        categories = (Category.objects.get_categories_for_nav())
        product = LatestProducts.objects.get_products_for_main_page('disinfectants', 'glassware', 'minimallyinvasiveurology')
        context = {
            'categories': categories,
            'all_product': product,
            'cart': self.cart
        }
        return render(request, 'base.html', context)


class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):

    CT_MODEL_MODEL_CLASS = {
        'minimallyinvasiveurology': MinimallyInvasiveUrology,
        'glassware': Glassware,
        'disinfectants': Disinfectants
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)

    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        context['cart'] = self.cart
        return context


class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class AddToCartView(AuthenticatedUserMixin, CartMixin, View):

    def get(self, request, **kwargs):

        print(kwargs.get('ct_model'))
        print(kwargs.get('slug'))
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        if created:
            self.cart.product.add(cart_product)
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар добавлен")
        return HttpResponseRedirect('/cart/')


# removing an item from the cart
class DeleteFromCartView(AuthenticatedUserMixin, CartMixin, View):

    def get(self, request, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        self.cart.product.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар удален")
        return HttpResponseRedirect('/cart/')


# changing the number of items in the cart
class ChangeQTYView(AuthenticatedUserMixin, CartMixin, View):

    def post(self, request, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Изменено кол-во товара")
        return HttpResponseRedirect('/cart/')


class CartView(AuthenticatedUserMixin, CartMixin, CategoryDetailMixin, View):

    def get(self, request):
        categories = (Category.objects.get_categories_for_nav())
        context = {
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'cart.html', context)


class CheckoutView(AuthenticatedUserMixin, CartMixin, CategoryDetailMixin, View):

    def get(self, request):
        categories = (Category.objects.get_categories_for_nav())
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form
        }
        return render(request, 'checkout.html', context)

# order creation
class MakeOrderView(AuthenticatedUserMixin, CartMixin, CategoryDetailMixin, View):

    @transaction.atomic
    def post(self, request):
        form = OrderForm(request.POST or None)
        client = Client.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.client = client
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            client.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Заказано!')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')


class LoginView(CartMixin, CategoryDetailMixin, View):

    def get(self, request):
        form = LoginForm(request.POST or None)
        categories = Category.objects.get_categories_for_nav()
        context = {'form': form, 'categories': categories, 'cart': self.cart}
        return render(request, 'profile/login.html', context)

    def post(self, request):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        context = {'form': form, 'cart': self.cart}
        return render(request, 'profile/login.html', context)


class RegistrationView(CartMixin, CategoryDetailMixin, View):
    def get(self, request):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.get_categories_for_nav()
        context = {'form': form, 'categories': categories, 'cart': self.cart}
        return render(request, 'profile/registration.html', context)

    def post(self, request):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Client.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect('/')
        context = {'form': form, 'cart': self.cart}
        return render(request, 'profile/registration.html', context)


class ProfileView(AuthenticatedUserMixin, CartMixin, CategoryDetailMixin, View):

    def get(self, request):
        client = Client.objects.get(user=request.user)
        orders = Order.objects.filter(client=client).order_by('-created_at')
        categories = Category.objects.get_categories_for_nav()
        return render(request, 'profile/profile.html', {'orders': orders, 'cart': self.cart, 'categories': categories})


class ProductCreateView(AuthenticatedSuperuserMixin, CreateView):

    CT_MODEL_FORM_CLASS = {
        'minimallyinvasiveurology': MinimallyInvasiveUrologyForm,
        'glassware': GlasswareForm,
        'disinfectants': DisinfectantsForm
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = kwargs.get('model')
        self.form_class = self.CT_MODEL_FORM_CLASS[kwargs['model']]
        return super().dispatch(request, *args, **kwargs)

    template_name = 'crud/crud_template.html'
    success_url = reverse_lazy('base')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_name'] = 'Добавить'
        if self.model == 'Glassware':
            context['title'] = 'Добавить товары лабораторной посуды'
        elif self.model == 'MinimallyInvasiveUrology':
            context['title'] = 'Добавить товары малоинвазивной урологии'
        if self.model == 'Disinfectants':
            context['title'] = 'Добавить товары дизенфицирующих средств'
        return context


class ProductDelete(AuthenticatedSuperuserMixin, View):

    def get(self, request, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        product.delete()
        messages.add_message(request, messages.INFO, "Товар удален из базы")
        return HttpResponseRedirect('/category/{}s/'.format(ct_model))


class ProductUpdateView(AuthenticatedSuperuserMixin, UpdateView):

    CT_MODEL_MODEL_CLASS = {
        'minimallyinvasiveurology': MinimallyInvasiveUrology,
        'glassware': Glassware,
        'disinfectants': Disinfectants
    }
    CT_MODEL_FORM_CLASS = {
        'minimallyinvasiveurology': MinimallyInvasiveUrologyForm,
        'glassware': GlasswareForm,
        'disinfectants': DisinfectantsForm
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        self.form_class = self.CT_MODEL_FORM_CLASS[kwargs['ct_model']]
        return super().dispatch(request, *args, **kwargs)

    template_name = 'crud/crud_template.html'
    success_url = reverse_lazy('base')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['button_name'] = 'Обновить'
        if self.model == 'Glassware':
            context['title'] = 'Обновить товар лабораторной посуды'
        elif self.model == 'MinimallyInvasiveUrology':
            context['title'] = 'Обновить товар малоинвазивной урологии'
        if self.model == 'Disinfectants':
            context['title'] = 'Обновить товар дезинфицирующих средств'
        return context


# displays a page with registered users
class UsersView(AuthenticatedSuperuserMixin, CartMixin, CategoryDetailMixin, View):
    def get(self, request):
        users = User.objects.all()
        categories = Category.objects.get_categories_for_nav()
        context = {
            'users': users,
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'profile/users.html', context)