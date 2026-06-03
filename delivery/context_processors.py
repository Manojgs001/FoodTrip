from .models import Customer, Cart

def cart_context(request):
    """Inject cart_count into every template automatically."""
    username = request.session.get('username')
    if username and username != 'admin':
        try:
            customer   = Customer.objects.get(username=username)
            cart       = Cart.objects.filter(customer=customer).first()
            cart_count = cart.item_count() if cart else 0
        except Customer.DoesNotExist:
            cart_count = 0
    else:
        cart_count = 0
    return {'cart_count': cart_count}
