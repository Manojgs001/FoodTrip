from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

from .models import Customer, Restaurant, Item, Cart, CartItem, Order, OrderItem
import os
from google import genai
import razorpay
from django.conf import settings

# ── helper ──────────────────────────────────────────────
def get_username(request):
    """Return logged-in username from session, or None."""
    return request.session.get('username')

def login_required_customer(view_fn):
    """Simple decorator: redirect to signin if not logged in."""
    def wrapper(request, *args, **kwargs):
        if not get_username(request):
            messages.error(request, 'Please sign in to continue.')
            return redirect('open_signin')
        return view_fn(request, *args, **kwargs)
    return wrapper

def admin_required(view_fn):
    """Decorator: only allow the admin session through; redirect others to signin."""
    def wrapper(request, *args, **kwargs):
        if get_username(request) != 'admin':
            messages.error(request, 'Admin access only.')
            return redirect('open_signin')
        return view_fn(request, *args, **kwargs)
    return wrapper

# Create your views here.
def custom_404(request, exception=None):
    return render(request, 'delivery/404.html', status=404)

def index(request):
    return render(request, 'delivery/index.html')

def open_signin(request):
    return render(request, 'delivery/signin.html')

def open_signup(request):
    return render(request, 'delivery/signup.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email    = request.POST.get('email')
        mobile   = request.POST.get('mobile')
        address  = request.POST.get('address')

        # Block reserved username
        if username.lower() == 'admin':
            messages.error(request, 'The username "admin" is reserved. Please choose a different one.')
            return redirect('open_signup')

        if Customer.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken. Please choose a different one.')
            return redirect('open_signup')
        Customer.objects.create(
            username = username,
            password = make_password(password),   # hashed ✅
            email    = email,
            mobile   = mobile,
            address  = address,
        )
        messages.success(request, 'Account created successfully! Please sign in.')
    return redirect('open_signin')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Admin special case
        if username == 'admin' and password == 'admin':
            request.session['username'] = 'admin'
            return redirect('open_show_restaurant')

        try:
            customer = Customer.objects.get(username=username)
            if check_password(password, customer.password):
                request.session['username'] = username
                return redirect('customer_home')
            else:
                # Support legacy plain-text passwords (for existing data)
                if customer.password == password:
                    # Upgrade to hashed on next login
                    customer.password = make_password(password)
                    customer.save()
                    request.session['username'] = username
                    return redirect('customer_home')
                messages.error(request, 'Invalid username or password. Please try again.')
                return redirect('open_signin')
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('open_signin')
    return redirect('open_signin')

def logout(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('open_signin')
    
@admin_required
def open_add_restaurant(request):
    return render(request, 'delivery/add_restaurant.html', {"username": "admin"})

@admin_required
def add_restaurant(request):
    if request.method == 'POST':
        name    = request.POST.get('name')
        cuisine = request.POST.get('cuisine')
        rating  = request.POST.get('rating')
        picture = request.FILES.get('picture')  # uploaded file

        if Restaurant.objects.filter(name=name).exists():
            messages.error(request, f'A restaurant named "{name}" already exists.')
            return redirect('open_add_restaurant')
        Restaurant.objects.create(
            name    = name,
            picture = picture,
            cuisine = cuisine,
            rating  = rating,
        )
        messages.success(request, f'Restaurant "{name}" added successfully!')
    return render(request, 'delivery/admin_home.html', {"username": "admin"})

@admin_required
def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList, "username": "admin"})

@admin_required
def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    return render(request, 'delivery/update_restaurant.html', {"restaurant" : restaurant, "username": "admin"})

@admin_required
def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        restaurant.name    = request.POST.get('name')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating  = request.POST.get('rating')
        if request.FILES.get('picture'):          # new file uploaded
            restaurant.picture = request.FILES['picture']
        # if no new file, keep existing picture
        restaurant.save()
        messages.success(request, f'Restaurant "{restaurant.name}" updated successfully!')

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList, "username": "admin"})


@admin_required
def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(request, 'delivery/show_restaurants.html',{"restaurantList" : restaurantList, "username": "admin"})


@admin_required
def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'delivery/update_menu.html',{"itemList" : itemList, "restaurant" : restaurant, "username": "admin"})
    
@admin_required
def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)

    if request.method == 'POST':
        name        = request.POST.get('name')
        description = request.POST.get('description')
        price       = request.POST.get('price')
        vegeterian  = request.POST.get('vegeterian') == 'on'
        picture     = request.FILES.get('picture')        # uploaded file
        picture_url = request.POST.get('picture_url', '').strip()  # pasted URL

        if Item.objects.filter(name=name, restaurant=restaurant).exists():
            messages.error(request, f'An item named "{name}" already exists in this restaurant\'s menu.')
            return redirect('open_update_menu', restaurant_id=restaurant.id)

        item = Item.objects.create(
            restaurant  = restaurant,
            name        = name,
            description = description,
            price       = price,
            vegeterian  = vegeterian,
            picture     = picture,   # file upload (may be None)
        )
        # If no file uploaded but a URL was pasted, store it directly
        if not picture and picture_url:
            item.picture = picture_url
            item.save(update_fields=['picture'])

        messages.success(request, f'Menu item "{name}" added successfully!')
    return redirect('open_update_menu', restaurant_id=restaurant.id)

@admin_required
def edit_menu_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        item.name        = request.POST.get('name')
        item.description = request.POST.get('description')
        item.price       = request.POST.get('price')
        item.vegeterian  = request.POST.get('vegeterian') == 'on'
        picture_url      = request.POST.get('picture_url', '').strip()
        if request.FILES.get('picture'):     # file upload takes priority
            item.picture = request.FILES['picture']
        elif picture_url:                    # URL pasted by admin
            item.picture = picture_url
        # else: keep existing picture unchanged
        item.save()
        messages.success(request, f'Menu item "{item.name}" updated successfully!')
        return redirect('open_update_menu', restaurant_id=item.restaurant.id)
    # GET — return item data as JSON for the modal
    from django.http import JsonResponse
    return JsonResponse({
        'id':            item.id,
        'name':          item.name,
        'description':   item.description,
        'price':         item.price,
        'vegeterian':    item.vegeterian,
        'picture_url':   item.picture.url if item.picture else '',
        'restaurant_id': item.restaurant.id,
    })

@admin_required
def delete_menu_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    restaurant_id = item.restaurant.id
    item_name = item.name
    item.delete()
    messages.success(request, f'Menu item "{item_name}" deleted successfully!')
    return redirect('open_update_menu', restaurant_id=restaurant_id)


def customer_home(request):
    username = get_username(request)
    if not username or username == 'admin':
        return redirect('open_signin')

    query   = request.GET.get('q', '').strip()
    cuisine = request.GET.get('cuisine', '').strip()

    restaurantList = Restaurant.objects.all()
    if query:
        restaurantList = restaurantList.filter(name__icontains=query)
    if cuisine:
        restaurantList = restaurantList.filter(cuisine__icontains=cuisine)

    # Pass all distinct cuisines for the filter dropdown
    all_cuisines = Restaurant.objects.values_list('cuisine', flat=True).distinct()

    # Pass customer's existing ratings so stars show on cards
    customer = Customer.objects.filter(username=username).first()
    from .models import Rating
    user_ratings = {}
    if customer:
        for r in Rating.objects.filter(customer=customer):
            user_ratings[r.restaurant_id] = r.stars

    return render(request, 'delivery/customer_home.html', {
        'restaurantList': restaurantList,
        'username':       username,
        'query':          query,
        'cuisine':        cuisine,
        'all_cuisines':   all_cuisines,
        'user_ratings':   user_ratings,
    })

def view_menu(request, restaurant_id):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    restaurant = Restaurant.objects.get(id=restaurant_id)
    itemList   = restaurant.items.all()
    return render(request, 'delivery/customer_menu.html', {
        'itemList': itemList, 'restaurant': restaurant, 'username': username
    })

def add_to_cart(request, item_id):
    username = get_username(request)
    if not username:
        return JsonResponse({'status': 'error', 'message': 'Not logged in'}, status=401)
    item     = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)
    cart, _  = Cart.objects.get_or_create(customer=customer)

    # Use CartItem to track quantity
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Keep M2M in sync (used by checkout flow)
    cart.items.add(item)

    total_items = sum(ci.quantity for ci in cart.cart_items.all())
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'cart_count': total_items})
    return redirect('show_cart')

def remove_from_cart(request, item_id):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    cart     = Cart.objects.filter(customer=customer).first()
    if cart:
        CartItem.objects.filter(cart=cart, item_id=item_id).delete()
        cart.items.remove(item_id)  # keep M2M in sync
    return redirect('show_cart')

def update_cart_quantity(request, item_id):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    action   = request.POST.get('action')   # 'increase' or 'decrease'
    customer = get_object_or_404(Customer, username=username)
    cart     = Cart.objects.filter(customer=customer).first()
    if cart:
        try:
            ci = CartItem.objects.get(cart=cart, item_id=item_id)
            if action == 'increase':
                ci.quantity += 1
                ci.save()
            elif action == 'decrease':
                if ci.quantity > 1:
                    ci.quantity -= 1
                    ci.save()
                else:
                    ci.delete()
                    cart.items.remove(item_id)
        except CartItem.DoesNotExist:
            pass
    return redirect('show_cart')

def show_cart(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer    = get_object_or_404(Customer, username=username)
    cart        = Cart.objects.filter(customer=customer).first()
    cart_items  = cart.cart_items.select_related('item').all() if cart else []
    total_price = cart.total_price() if cart else 0
    return render(request, 'delivery/cart.html', {
        'cart_items':  cart_items,
        'total_price': total_price,
        'username':    username,
    })

def profile(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    if request.method == 'POST':
        customer.email   = request.POST.get('email', customer.email)
        customer.mobile  = request.POST.get('mobile', customer.mobile)
        customer.address = request.POST.get('address', customer.address)
        new_password     = request.POST.get('new_password')
        if new_password:
            customer.password = make_password(new_password)
        customer.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'delivery/profile.html', {'customer': customer, 'username': username})

# Checkout View
def checkout(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer   = get_object_or_404(Customer, username=username)
    cart       = Cart.objects.filter(customer=customer).first()
    # Use CartItem for quantities; fall back to M2M items for Razorpay flow
    cart_items  = cart.cart_items.select_related('item').all() if cart else []
    total_price = cart.total_price() if cart else 0

    # Fix 4: Empty cart guard — redirect back to cart with a message
    if total_price == 0:
        messages.error(request, 'Your cart is empty! Add some items before checking out.')
        return redirect('show_cart')

    # Fix 2: Only create a new Razorpay/DB order if one isn't already pending for this session
    existing_order = Order.objects.filter(
        customer=customer, status='Pending'
    ).order_by('-created_at').first()

    mock_mode = False
    order_id  = "mock_order_id_for_testing"

    if existing_order:
        # Reuse the existing pending order — no duplicate creation
        order_id  = existing_order.razorpay_order_id or order_id
        mock_mode = (order_id == "mock_order_id_for_testing")
    else:
        # Create a fresh Razorpay order
        try:
            if settings.RAZORPAY_KEY_SECRET == 'YOUR_SECRET_KEY':
                raise Exception("Mock mode")
            client     = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order_data = {'amount': int(total_price * 100), 'currency': 'INR'}
            rp_order   = client.order.create(data=order_data)
            order_id   = rp_order['id']
        except Exception:
            mock_mode = True

        Order.objects.create(
            customer=customer, total_price=total_price,
            status='Pending', razorpay_order_id=order_id
        )

    # Build a simple list of dicts for the template (name, price, quantity)
    summary_items = [
        {'name': ci.item.name, 'price': ci.item.price, 'quantity': ci.quantity}
        for ci in cart_items
    ]

    return render(request, 'delivery/checkout.html', {
        'username':        username,
        'cart_items':      summary_items,
        'total_price':     total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id':        order_id,
        'amount':          total_price,
        'amount_paise':    int(total_price * 100),   # Razorpay needs integer paise
        'mock_mode':       mock_mode,
    })


# Orders Page
def orders(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    cart     = Cart.objects.filter(customer=customer).first()

    cart_items  = []
    total_price = 0
    status      = 'pending'
    error_msg   = None

    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id   = request.POST.get('razorpay_order_id', '')
        signature  = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id':   order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature':  signature
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            if payment_id == "mock_payment_id_for_testing":
                pass
            else:
                client.utility.verify_payment_signature(params_dict)

            db_order = Order.objects.filter(razorpay_order_id=order_id).first()
            if db_order:
                db_order.status = 'Paid'
                db_order.razorpay_payment_id = payment_id
                db_order.save()

            if cart:
                cart_item_qs = cart.cart_items.select_related('item').all()
                total_price  = cart.total_price()
                if db_order:
                    # Fix 3: Save correct quantity per item from CartItem
                    for ci in cart_item_qs:
                        OrderItem.objects.create(
                            order             = db_order,
                            item              = ci.item,
                            price_at_purchase = ci.item.price,
                            quantity          = ci.quantity,
                        )
                # Clear both CartItem records and the M2M relation
                cart.cart_items.all().delete()
                cart.items.clear()
            status = 'success'
        except razorpay.errors.SignatureVerificationError:
            status    = 'failed'
            error_msg = 'Payment verification failed. The signature is invalid or tampered with.'
    else:
        status = 'view_only'

    return render(request, 'delivery/orders.html', {
        'username':    username,
        'customer':    customer,
        'cart_items':  cart_items,
        'total_price': total_price,
        'status':      status,
        'error':       error_msg,
    })

# Order History Page
def order_history(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    customer = get_object_or_404(Customer, username=username)
    orders   = Order.objects.filter(customer=customer).order_by('-created_at')
    return render(request, 'delivery/order_history.html', {
        'username': username,
        'orders':   orders,
    })

# Admin Dashboard
@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'delivery/admin_orders.html', {'orders': orders, 'username': 'admin'})

@admin_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
    return redirect('admin_orders')

# AI Feature
def crave_detector(request):
    username = get_username(request)
    if not username:
        return redirect('open_signin')
    response_text = None
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        items  = Item.objects.select_related('restaurant').all()
        menu_context = "Available Menu Items:\n"
        for i in items:
            menu_context += f"- {i.name} at {i.restaurant.name} (₹{i.price}): {i.description}\n"

        system_instruction = "You are the 'Crave Detector', an expert AI food recommender for the FoodTrip platform. Based on the user's craving and the provided menu context, recommend 1 or 2 specific items from the menu. Be fun, appetising, and very brief (max 3 sentences)."

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            response_text = "Error: GEMINI_API_KEY is not set in the .env file."
        else:
            try:
                client   = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"{menu_context}\n\nUser Craving: {prompt}",
                    config=genai.types.GenerateContentConfig(system_instruction=system_instruction)
                )
                response_text = response.text
            except Exception as e:
                response_text = f"An API error occurred: {str(e)}"

    return render(request, 'delivery/crave_detector.html', {'username': username, 'response': response_text})


# ── Inline AI Suggest (AJAX — called from home page search bar) ──────────────
@login_required_customer
def ai_suggest_inline(request):
    """AJAX POST: returns AI suggestion + matched dish items for Add to Cart."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    prompt = request.POST.get('prompt', '').strip()
    if not prompt:
        return JsonResponse({'error': 'Empty prompt'}, status=400)

    all_items    = Item.objects.select_related('restaurant').all()
    menu_context = "Available Menu Items:\n"
    for i in all_items:
        menu_context += f"- {i.name} at {i.restaurant.name} (Rs.{i.price}): {i.description}\n"

    system_instruction = (
        "You are the 'Crave Detector' on FoodTrip. "
        "Given the user's craving, recommend 1-2 specific dishes from the menu. "
        "Be fun and concise (max 2 sentences). "
        "Then on a new line write: DISHES: <exact dish name 1>, <exact dish name 2> "
        "Then on a new line write: RESTAURANTS: <restaurant name 1>, <restaurant name 2>"
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return JsonResponse({'error': 'API key not configured'}, status=500)

    try:
        client   = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{menu_context}\n\nUser Craving: {prompt}",
            config=genai.types.GenerateContentConfig(system_instruction=system_instruction)
        )
        text = response.text or ''

        # Parse suggestion, dish names, restaurant names
        suggestion    = text
        dish_names    = []
        rest_names    = []

        if 'DISHES:' in text:
            parts      = text.split('DISHES:')
            suggestion = parts[0].strip()
            remainder  = parts[1]
            if 'RESTAURANTS:' in remainder:
                dish_part, rest_part = remainder.split('RESTAURANTS:', 1)
                dish_names = [d.strip() for d in dish_part.split(',') if d.strip()]
                rest_names = [r.strip() for r in rest_part.split(',') if r.strip()]
            else:
                dish_names = [d.strip() for d in remainder.split(',') if d.strip()]
        elif 'RESTAURANTS:' in text:
            parts      = text.split('RESTAURANTS:')
            suggestion = parts[0].strip()
            rest_names = [r.strip() for r in parts[1].split(',') if r.strip()]

        # Match dish names to real DB items (fuzzy case-insensitive)
        matched_items = []
        for dish in dish_names:
            dish_lower = dish.lower()
            for item in all_items:
                if dish_lower in item.name.lower() or item.name.lower() in dish_lower:
                    matched_items.append({
                        'id':         item.id,
                        'name':       item.name,
                        'price':      str(item.price),
                        'restaurant': item.restaurant.name,
                        'picture':    item.get_picture_url() if hasattr(item, 'get_picture_url') else '',
                        'add_url':    f'/add_to_cart/{item.id}',
                        'menu_url':   f'/menu/{item.restaurant.id}/',
                    })
                    break   # one match per dish name

        return JsonResponse({
            'suggestion':  suggestion,
            'restaurants': rest_names,
            'items':       matched_items,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── Rating view ─────────────────────────────────────────────────────────────
@login_required_customer
def rate_restaurant(request, restaurant_id):
    """AJAX POST: save/update a 1-5 star rating for a restaurant."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST only'}, status=405)
    from .models import Rating
    username   = get_username(request)
    customer   = get_object_or_404(Customer, username=username)
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    stars      = int(request.POST.get('stars', 0))
    if not 1 <= stars <= 5:
        return JsonResponse({'status': 'error', 'message': 'Stars must be 1-5'}, status=400)

    rating, _ = Rating.objects.update_or_create(
        customer=customer, restaurant=restaurant,
        defaults={'stars': stars}
    )
    # Recalculate average and update restaurant.rating
    from django.db.models import Avg
    avg = Rating.objects.filter(restaurant=restaurant).aggregate(Avg('stars'))['stars__avg']
    restaurant.rating = round(avg, 1)
    restaurant.save(update_fields=['rating'])
    return JsonResponse({'status': 'success', 'new_avg': restaurant.rating, 'user_stars': stars})


# ── Admin Dashboard ──────────────────────────────────────────────────────────
@admin_required
def admin_dashboard(request):
    from django.db.models import Sum, Count, Avg
    from .models import Rating

    total_orders   = Order.objects.count()
    total_revenue  = Order.objects.filter(status__in=['Paid','Delivered']).aggregate(
                         total=Sum('total_price'))['total'] or 0
    total_customers = Customer.objects.count()
    total_items     = Item.objects.count()

    # Top 5 restaurants by order count
    top_restaurants = (
        Restaurant.objects
        .annotate(order_count=Count('items__cart_entries__cart__customer__orders', distinct=True))
        .order_by('-order_count')[:5]
    )

    # Recent 10 orders
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]

    # Orders by status
    status_counts = {
        s: Order.objects.filter(status=s).count()
        for s, _ in Order.STATUS_CHOICES
    }

    return render(request, 'delivery/admin_dashboard.html', {
        'username':        'admin',
        'total_orders':    total_orders,
        'total_revenue':   total_revenue,
        'total_customers': total_customers,
        'total_items':     total_items,
        'top_restaurants': top_restaurants,
        'recent_orders':   recent_orders,
        'status_counts':   status_counts,
    })