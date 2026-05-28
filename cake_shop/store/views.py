from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User, Product, Cart, Flavour
import json

def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})


def register(request):
    if request.method == "POST":
        User.objects.create(
            username=request.POST['username'],
            name=request.POST['name'],
            email=request.POST['email'],
            address=request.POST['address'],
            phone=request.POST['phone'],
            password=request.POST['password'],
            profile_pic=request.FILES.get('profile_pic')
        )
        return redirect('login')
    return render(request, 'register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')

        try:
            u = User.objects.get(username=username, password=password)
            request.session['user_id'] = u.id
            return redirect('user_dashboard')
        except:
            return render(request, 'login.html', {'error': 'Invalid Username or Password'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')
    products = Product.objects.all()
    users_count = User.objects.filter(role='user').count()
    return render(request, 'admin/dashboard.html', {
        'products': products,
        'users_count': users_count,
    })

@login_required
def add_category(request):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        if name:
            if Flavour.objects.filter(name__iexact=name).exists():
                messages.error(request, f'Category "{name}" already exists!')
            else:
                Flavour.objects.create(name=name)
                messages.success(request, f'Category "{name}" added successfully!')
        return redirect('add_category')

    flavours = Flavour.objects.all().order_by('name')
    return render(request, 'admin/add_category.html', {'flavours': flavours})


@login_required
def delete_category(request, id):
    if not request.user.is_superuser:
        return redirect('login')
    flavour = get_object_or_404(Flavour, id=id)
    flavour.delete()
    messages.success(request, 'Category deleted.')
    return redirect('add_category')

@login_required
def add_product(request):
    if not request.user.is_superuser:
        return redirect('login')

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        flavour_name = request.POST.get("flavour", "").strip()
        price = request.POST.get("price")
        image = request.FILES.get("image")
        description = request.POST.get("description")
        if Product.objects.filter(name__iexact=name).exists():
            flavours = Flavour.objects.all().order_by('name')
            return render(request, "admin/add_product.html", {
                'flavours': flavours,
                'error': f'A product named "{name}" already exists.',
                'form_data': request.POST 
            })

        flavour, created = Flavour.objects.get_or_create(
            name__iexact=flavour_name,
            defaults={'name': flavour_name}
        )
        if not created:
            flavour = Flavour.objects.get(name__iexact=flavour_name)

        Product.objects.create(
            name=name, flavour=flavour,
            price=price, image=image, description=description
        )
        return redirect("view_products")

    flavours = Flavour.objects.all().order_by('name')
    return render(request, "admin/add_product.html", {'flavours': flavours})

@login_required
def view_products(request):
    if not request.user.is_superuser:
        return redirect('login')
    products = Product.objects.all().select_related('flavour')
    return render(request, 'admin/view_products.html', {'products': products})

@login_required
def view_users(request):
    if not request.user.is_superuser:
        return redirect('login')
    users = User.objects.filter(role='user').order_by('id')
    return render(request, 'admin/view_users.html', {'users': users})

@login_required
def admin_profile(request):
    if not request.user.is_superuser:
        return redirect('login')
    return render(request, 'admin/admin_profile.html')


@login_required
def edit_admin_profile(request):
    if not request.user.is_superuser:
        return redirect('login')
    user = request.user
    if request.method == "POST":
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.save()
        messages.success(request, "Profile Updated Successfully!")
        return redirect('admin_profile')
    return render(request, 'admin/edit_admin_profile.html')


@login_required
def change_admin_password(request):
    if not request.user.is_superuser:
        return redirect('login')
    if request.method == "POST":
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')
        user = request.user
        if not user.check_password(current):
            messages.error(request, "Current password incorrect")
            return redirect('change_admin_password')
        if new != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('change_admin_password')
        user.set_password(new)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed successfully!")
        return redirect('admin_profile')
    return render(request, 'admin/change_password.html')


@login_required
def edit_product(request, id):
    if not request.user.is_superuser:
        return redirect('login')
    product = get_object_or_404(Product, id=id)
    flavours = Flavour.objects.all()

    if request.method == "POST":
        product.name = request.POST.get('name')
        flavour_name = request.POST.get('flavour', '').strip()
        flavour, _ = Flavour.objects.get_or_create(
            name__iexact=flavour_name,
            defaults={'name': flavour_name}
        )
        product.flavour = flavour
        product.price = request.POST.get('price')
        product.description = request.POST.get('description', '')
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        return redirect('view_products')

    return render(request, 'admin/edit_product.html', {
        'product': product,
        'flavours': flavours
    })


@login_required
def delete_product(request, id):
    if not request.user.is_superuser:
        return redirect('login')
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('view_products')


def user_dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = User.objects.get(id=request.session['user_id'])
    products = Product.objects.all()
    flavours = Flavour.objects.all()   # changed from filter(product__isnull=False)
    cart_count = Cart.objects.filter(user=user).count()
    return render(request, 'user/dashboard.html', {
        'products': products,
        'flavours': flavours,
        'user': user,
        'cart_count': cart_count
    })


def add_cart(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        product_id = request.POST.get('id')
        product = Product.objects.get(id=product_id)
        Cart.objects.create(user=user, product=product)
        count = Cart.objects.filter(user=user).count()
        return JsonResponse({'msg': 'Added to cart successfully', 'count': count})


def cart_page(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = User.objects.get(id=request.session['user_id'])
    cart_items = Cart.objects.filter(user=user)
    total = sum([c.total_amount() for c in cart_items])
    cart_count = Cart.objects.filter(user=user).count()
    return render(request, 'user/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count,
        'user': user
    })

def update_cart(request):
    if request.method == "POST":
        cart_id = request.POST.get('cart_id')
        action = request.POST.get('action')
        cart = Cart.objects.get(id=cart_id)
        if action == "increase":
            cart.quantity += 1
        else:
            cart.quantity -= 1
            if cart.quantity <= 0:
                cart.delete()
                user_id = request.session.get('user_id')
                user = User.objects.get(id=user_id)
                grand_total = sum([c.total_amount() for c in Cart.objects.filter(user=user)])
                return JsonResponse({'status': 'deleted', 'grand_total': grand_total})
        cart.save()
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        grand_total = sum([c.total_amount() for c in Cart.objects.filter(user=user)])
        return JsonResponse({'quantity': cart.quantity, 'amount': cart.total_amount(), 'grand_total': grand_total})


def delete_cart(request, id):
    Cart.objects.filter(id=id).delete()
    return redirect('cart')

def payment_page(request, id):
    product = Product.objects.get(id=id)
    return render(request, 'user/payment.html', {'product': product})


def search_cake(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(flavour__name__icontains=query)
    cart_count = 0
    user = None
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart_count = Cart.objects.filter(user=user).count()
    flavours = Flavour.objects.all()   # changed
    return render(request, 'user/dashboard.html', {
        'products': products,
        'flavours': flavours,
        'cart_count': cart_count,
        'user': user
    })

def flavour_cakes(request, id):
    flavour = get_object_or_404(Flavour, id=id)
    products = Product.objects.filter(flavour_id=id)
    flavours = Flavour.objects.all()   # show ALL flavours, not just ones with products
    cart_count = 0
    user = None
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart_count = Cart.objects.filter(user=user).count()
    return render(request, 'user/dashboard.html', {
        'products': products,
        'flavours': flavours,
        'cart_count': cart_count,
        'user': user,
        'selected_flavour': flavour,
    })

def view_profile(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = User.objects.get(id=request.session['user_id'])
    flavours = Flavour.objects.filter(product__isnull=False).distinct()
    cart_count = Cart.objects.filter(user=user).count()
    return render(request, 'user/view_profile.html', {
        'user': user,
        'flavours': flavours,
        'cart_count': cart_count
    })

def edit_profile(request):
    if 'user_id' not in request.session:
        return redirect('login')

    user = User.objects.get(id=request.session['user_id'])

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        name     = request.POST.get('name')
        email    = request.POST.get('email')
        address  = request.POST.get('address')
        phone    = request.POST.get('phone')

        errors = {}
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            errors['username'] = 'This username is already taken.'
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            errors['email'] = 'This email is already used by another account.'
        if User.objects.filter(phone=phone).exclude(id=user.id).exists():
            errors['phone'] = 'This phone number is already used by another account.'

        if errors:
            return render(request, 'user/edit_profile.html', {
                'user': user,
                'errors': errors
            })

        user.username = username
        user.name     = name
        user.email    = email
        user.address  = address
        user.phone    = phone
        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES.get('profile_pic')
        user.save()
        return redirect('view_profile')

    return render(request, 'user/edit_profile.html', {'user': user})


def cart_count_api(request):
    if 'user_id' not in request.session:
        return JsonResponse({'count': 0})
    user = User.objects.get(id=request.session['user_id'])
    count = Cart.objects.filter(user=user).count()
    return JsonResponse({'count': count})


def add_to_cart(request, id):
    if 'user_id' not in request.session:
        return JsonResponse({'status': 'login_required'})
    user = User.objects.get(id=request.session['user_id'])
    product = Product.objects.get(id=id)
    Cart.objects.create(user=user, product=product)
    count = Cart.objects.filter(user=user).count()
    return JsonResponse({'status': 'success', 'count': count})


def buy_single(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id)
    request.session['buy_type'] = 'single'
    request.session['cart_id'] = cart_id
    return redirect('payment')

def buy_all(request):
    request.session['buy_type'] = 'all'
    return redirect('payment')


def payment(request):
    buy_type = request.session.get('buy_type')
    if buy_type == 'single':
        cart_id = request.session.get('cart_id')
        cart_item = Cart.objects.get(id=cart_id)
        total = cart_item.total_amount()
        items = [cart_item]
    else:
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        items = Cart.objects.filter(user=user)
        total = sum([c.total_amount() for c in items])
    return render(request, 'user/payment.html', {'items': items, 'total': total})


def change_user_password(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user = User.objects.get(id=request.session['user_id'])
    if request.method == "POST":
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')
        if user.password != current:
            messages.error(request, "Current password is incorrect")
            return redirect('change_password')
        if new != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('change_password')
        user.password = new
        user.save()
        messages.success(request, "Password changed successfully!")
        return redirect('login')
    return render(request, 'user/change_password.html', {'user': user})


@csrf_exempt
def check_user_exists(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        return JsonResponse({
            'username_exists': User.objects.filter(username=username).exists(),
            'email_exists': User.objects.filter(email=email).exists(),
            'phone_exists': User.objects.filter(phone=phone).exists()
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def check_current_password(request):
    if request.method == 'POST':
        if 'user_id' not in request.session:
            return JsonResponse({'valid': False})
        user = User.objects.get(id=request.session['user_id'])
        entered = request.POST.get('current_password', '')
        return JsonResponse({'valid': user.password == entered})
    return JsonResponse({'valid': False})


def place_order(request):
    if request.method == "POST":
        buy_type = request.session.get('buy_type')
        if buy_type == 'single':
            cart_id = request.session.get('cart_id')
            Cart.objects.filter(id=cart_id).delete()
            request.session.pop('cart_id', None)
        else:
            user_id = request.session.get('user_id')
            user = User.objects.get(id=user_id)
            Cart.objects.filter(user=user).delete()
        request.session.pop('buy_type', None)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_user(request, id):
    if not request.user.is_superuser:
        return redirect('login')
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('view_users')