from django.contrib import admin
from .models import User, Product, Cart, Flavour

admin.site.register(User)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Flavour)
