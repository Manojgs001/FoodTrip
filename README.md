# 🍕 FoodTrip — Full-Stack Food Delivery Web App

A full-stack food delivery platform built with **Django**, featuring restaurant browsing, cart management, Razorpay payments, AI-powered recommendations, and a complete admin panel.

> Built as a portfolio project to demonstrate full-stack Django development skills.

---

## 🌐 Live Demo

> _Coming soon — deploying to Render_

---

## ✨ Features

### 👤 Customer Side
- **Signup / Login / Logout** — Session-based authentication
- **Browse Restaurants** — Search by name, filter by cuisine type
- **View Menus** — Browse items with Veg/Non-Veg badges and prices
- **Cart System** — Add/remove items, update quantities, live cart count badge
- **Razorpay Checkout** — Secure payment integration with real test credentials
- **Order History** — Visual step-by-step order status tracker (Paid → Preparing → Out for Delivery → Delivered)
- **Star Ratings** — Rate restaurants 1–5 stars (AJAX, no page reload)
- **AI Crave Detector** — Tell the AI your mood, it suggests what to eat (Gemini API)
- **Profile Page** — View and manage account details
- **Dark Mode** — Toggle between light and dark themes (saved to localStorage)

### 🛠 Admin Side
- **Dashboard** — Total orders, revenue, customers, menu items at a glance
- **Manage Restaurants** — Add, edit, delete restaurants with image upload
- **Manage Menu Items** — Add/edit/delete items with prices and images
- **Order Management** — View all customer orders and update status

### 💅 UI/UX
- Premium design with **Outfit** Google Font
- Smooth card animations and hover effects
- Mobile responsive with hamburger menu
- Animated empty states and cart badge

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.x (Python) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML, CSS (Vanilla), JavaScript |
| **Payments** | Razorpay Payment Gateway |
| **AI** | Google Gemini API |
| **Auth** | Session-based (custom, no django.contrib.auth) |
| **Deployment** | Render (with build.sh) |

---

## 📁 Project Structure

```
FoodTrip/
├── FoodBuddy/              # Django project settings & URLs
│   ├── settings.py
│   └── urls.py
├── delivery/               # Main Django app
│   ├── models.py           # Customer, Restaurant, Item, Cart, Order, Rating
│   ├── views.py            # All view logic
│   ├── urls.py             # URL routing
│   ├── context_processors.py  # Global cart count
│   ├── templatetags/       # Custom template filters
│   ├── templates/delivery/ # All HTML templates
│   └── static/delivery/    # CSS and images
├── manage.py
├── requirements.txt
└── build.sh                # Render deployment script
```

---

## ⚙️ Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Manojgs001/FoodTrip.git
cd FoodTrip

# 2. Create virtual environment
python -m venv myenv
myenv\Scripts\activate        # Windows
# source myenv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Add your Razorpay and Gemini API keys

# 5. Run migrations
python manage.py migrate

# 6. Start the server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_django_secret_key
```

---

## 💳 Test Payment (Razorpay)

Use these test credentials on the payment screen:

| Field | Value |
|---|---|
| Card Number | `4111 1111 1111 1111` |
| Expiry | Any future date |
| CVV | Any 3 digits |
| OTP | `1234` |

---

## 🔐 Admin Login

```
Username: admin
Password: admin
```

---

## 📦 Key Models

```python
Customer     # username, password, email, phone
Restaurant   # name, cuisine, rating, picture
Item         # name, price, description, vegeterian, picture → Restaurant
Cart         # customer → Restaurant (one active cart per customer)
CartItem     # cart, item, quantity
Order        # customer, total_price, status, razorpay_payment_id
OrderItem    # order, item, quantity, price_at_purchase
Rating       # customer, restaurant, stars (1–5)
```

---

## 🤝 Connect

**Manoj Kumar** — Fresher Full-Stack Developer

[![GitHub](https://img.shields.io/badge/GitHub-Manojgs001-181717?logo=github)](https://github.com/Manojgs001)

---

*Built with Django + lots of chai ☕*
