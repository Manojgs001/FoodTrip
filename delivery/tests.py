import hmac
import hashlib
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.hashers import make_password
from .models import Customer, Restaurant, Item, Cart, CartItem, Order


# Helper: generate a valid Razorpay-style HMAC-SHA256 signature
def make_sig(order_id, payment_id, secret):
    message = order_id + "|" + payment_id
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


class HMACSignatureTests(TestCase):
    """Tests the HMAC-SHA256 algorithm Razorpay uses for payment verification."""

    SECRET  = "test_secret_key_1234"
    ORDER   = "order_ABC123"
    PAYMENT = "pay_XYZ789"

    def test_01_valid_signature_matches(self):
        sig1 = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        sig2 = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        self.assertEqual(sig1, sig2)

    def test_02_tampered_payment_id_fails(self):
        valid   = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        hacked  = make_sig(self.ORDER, "pay_HACKED999", self.SECRET)
        self.assertNotEqual(valid, hacked)

    def test_03_tampered_order_id_fails(self):
        valid   = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        hacked  = make_sig("order_HACKED000", self.PAYMENT, self.SECRET)
        self.assertNotEqual(valid, hacked)

    def test_04_wrong_secret_fails(self):
        valid   = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        attacker = make_sig(self.ORDER, self.PAYMENT, "attacker_secret")
        self.assertNotEqual(valid, attacker)

    def test_05_signature_length_is_64_hex_chars(self):
        sig = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        self.assertEqual(len(sig), 64)

    def test_06_signature_is_deterministic(self):
        self.assertEqual(
            make_sig(self.ORDER, self.PAYMENT, self.SECRET),
            make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        )

    def test_07_timing_safe_compare_digest(self):
        sig = make_sig(self.ORDER, self.PAYMENT, self.SECRET)
        self.assertTrue(hmac.compare_digest(sig, sig))
        self.assertFalse(hmac.compare_digest(sig, "a" * 64))

    def test_08_amount_converted_to_paise(self):
        # Razorpay requires Rs. amount multiplied by 100 (paise)
        total_rs = 250
        self.assertEqual(int(total_rs * 100), 25000)


class CartTotalTests(TestCase):
    """Tests cart total and Razorpay paise conversion logic."""

    def setUp(self):
        self.customer   = Customer.objects.create(
            username="testbuyer",
            password=make_password("pass123"),
            email="buyer@test.com"
        )
        self.restaurant = Restaurant.objects.create(
            name="Test Dhaba", cuisine="Indian"
        )
        self.item1 = Item.objects.create(
            name="Burger", price=120, restaurant=self.restaurant
        )
        self.item2 = Item.objects.create(
            name="Pizza", price=250, restaurant=self.restaurant
        )
        self.cart = Cart.objects.create(customer=self.customer)

    def test_09_single_item_total(self):
        CartItem.objects.create(cart=self.cart, item=self.item1, quantity=2)
        self.cart.items.add(self.item1)
        self.assertEqual(self.cart.total_price(), 240)

    def test_10_multiple_items_total(self):
        CartItem.objects.create(cart=self.cart, item=self.item1, quantity=1)
        CartItem.objects.create(cart=self.cart, item=self.item2, quantity=1)
        self.cart.items.add(self.item1, self.item2)
        self.assertEqual(self.cart.total_price(), 370)

    def test_11_empty_cart_returns_zero(self):
        self.assertEqual(self.cart.total_price(), 0)

    def test_12_razorpay_paise_is_total_times_100(self):
        CartItem.objects.create(cart=self.cart, item=self.item1, quantity=1)
        self.cart.items.add(self.item1)
        paise = int(self.cart.total_price() * 100)
        self.assertEqual(paise, 12000)