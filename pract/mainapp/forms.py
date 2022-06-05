from django import forms
from django.forms import ModelChoiceField
from django.contrib.auth.models import User
from .models import Order, Category, MinimallyInvasiveUrology, Disinfectants, Glassware

# order form
class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_date'].label = 'Дата получения заказа'
    order_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

    class Meta:
        model = Order
        fields = (
            'first_name', 'last_name', 'phone', 'address', 'buying_type', 'order_date', 'comment'
        )


class LoginForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'Пользователь {username} не найден')
        user = User.objects.filter(username=username).first()
        if user:
            if not user.check_password(password):
                raise forms.ValidationError('Неверный пароль')
        return self.cleaned_data

class RegistrationForm(forms.ModelForm):

    confirm_password = forms.CharField(widget=forms.PasswordInput)
    password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(required=False)
    address = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name', 'email', 'address', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        self.fields['confirm_password'].label = 'Подтвердите пароль'
        self.fields['phone'].label = 'Телефон'
        self.fields['address'].label = 'Адрес'
        self.fields['email'].label = 'Email'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамииля'

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f'Данный почтовый адрес уже зарегистрирован')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f'Логин {username} уже занят')
        return username

    def clean(self):

        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError('Пароли не совпадают')
        return self.cleaned_data

# MinimallyInvasiveUrology addition form
class MinimallyInvasiveUrologyForm(forms.ModelForm):

    category = ModelChoiceField(Category.objects.filter(slug='minimallyinvasiveurology'))

    class Meta:
        model = MinimallyInvasiveUrology
        fields = [
            'category', 'title', 'image', 'description', 'price', 'type', 'manufacturer', 'slug'
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label = 'Категория'

    def clean(self):
        return self.cleaned_data

# Disinfectants addition form
class DisinfectantsForm(forms.ModelForm):

    category = ModelChoiceField(Category.objects.filter(slug='disinfectants'))

    class Meta:
        model = Disinfectants
        fields = [
            'category', 'title', 'image', 'description', 'price', 'type', 'manufacturer', 'application', 'shelflife', 'slug'
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label = 'Категория'

    def clean(self):
        return self.cleaned_data

# Glassware addition form
class GlasswareForm(forms.ModelForm):

    category = ModelChoiceField(Category.objects.filter(slug='glassware'))

    class Meta:
        model = Glassware
        fields = [
            'category', 'title', 'image', 'description', 'price', 'type', 'manufacturer', 'amount', 'volume', 'slug'
        ]
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label = 'Категория'

    def clean(self):
        return self.cleaned_data

