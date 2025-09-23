# Animwear 🛍️

**Animwear** is a simple e-commerce platform built with **Django**, designed for anime fans. The platform allows users to browse, select, and purchase anime-themed merchandise, including t-shirts, hoodies, and more. Payments are seamlessly handled via **PayPal integration**.  

Anime lovers can now wear their favorite characters with pride!  

---

## Table of Contents

- [Features](#features)  
- [Demo](#demo)  
- [Tech Stack](#tech-stack)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Features

- Browse and search for anime-themed merchandise  
- Product details page with images and descriptions  
- Add products to a shopping cart  
- Checkout securely via PayPal  
- Responsive design for desktop and mobile  
- Admin panel to manage products, orders, and users  

---

## Demo

You can provide a link to a live demo (if hosted) or screenshots here:  

![Homepage](screenshots/homepage.png)  
![Product Page](screenshots/product_page.png)  
![Checkout](screenshots/checkout.png)  

---

## Tech Stack

- **Backend:** Django  
- **Frontend:** Django Templates (HTML, CSS, JS)  
- **Database:** SQLite (default for Django, can be changed to PostgreSQL)  
- **Payment Gateway:** PayPal  
- **Other Libraries:** Bootstrap (optional), Pillow (for image handling)  

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/animwear.git
cd animwear


python3 -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt


python manage.py migrate

python manage.py createsuperuser

python manage.py runserver


```

## Configuration

 # PayPal Integration:

Set up a PayPal Developer account: https://developer.paypal.com

## Usage

Browse products and add them to your cart.

Proceed to checkout and select PayPal as the payment method.

Complete your order via PayPal.

Admin can manage orders and products via Django admin panel.