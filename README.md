# e-commers — Pexo Market

Pexo Market is a React storefront backed by a Django REST API and a persistent
database. It includes a sample catalog, product search and category filters,
customer registration, and JWT sign-in.

## Run on Windows

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_products
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/` and
`http://127.0.0.1:8000/api/`; both return a status message and endpoint list.
The seed command creates 32 products in each of the Electronics, Home, Fashion,
and Kitchen categories, with a product-matched, credited photo for each item.
Re-run `python manage.py seed_products` to update the images of existing sample
items.

### Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/`. Vite proxies `/api` requests to Django.

## Database

MySQL is used by default. Configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, and `DB_PORT` in `backend/.env`; Django 5.2 supports MySQL 8.0.
For local development without MySQL, set `DB_ENGINE=sqlite` to use
`backend/db.sqlite3`. PostgreSQL is also supported through `DATABASE_URL`,
`POSTGRES_URL`, or `DATABASE_POSTGRES_URL`, which is used for the Vercel
production database.

## Customer API

- `POST /api/accounts/register/` — create an account
- `POST /api/accounts/login/` — sign in and receive JWT tokens
- `POST /api/accounts/google/` — verify a Google ID token and receive JWT tokens
- `POST /api/accounts/refresh/` — refresh an access token
- `GET /api/accounts/profile/` — read the authenticated customer profile
- `GET /api/products/` — list products; supports `search`, `category`, and
  `ordering`
- `GET /api/products/products/` — compatibility alias for the product list
- `GET /api/products/categories/` — list categories and product counts
- `GET /api/cart/` — read the authenticated customer's cart
- `POST /api/cart/sync/` — merge a saved guest cart into the customer's cart
- `POST /api/cart/add/` — add `{ "product_id": 1, "quantity": 1 }` to the cart
- `PUT /api/cart/items/<id>/` and `DELETE /api/cart/items/<id>/` — update or
  remove an owned cart item
- `POST /api/orders/checkout/` — atomically check stock, place an order,
  decrement inventory, and clear the cart
- `GET /api/orders/` and `GET /api/orders/<id>/` — list or read the customer's
  own orders (staff can view all orders)

Cart and order endpoints require a valid JWT. Checkout accepts `address`,
`city`, `state`, `postal_code`, `country`, and `phone`; orders are only created
when every cart item is in stock.

## Google sign-in

Google sign-in uses Google Identity Services in the frontend and verifies the
ID token on the Django backend. Create a Google OAuth **Web application**
client ID and add `http://localhost:5173` and `http://127.0.0.1:5173` as
authorized JavaScript origins. Set the same client ID in both:

- `backend/.env`: `GOOGLE_CLIENT_ID=your-web-client-id`
- `frontend/.env.local`: `VITE_GOOGLE_CLIENT_ID=your-web-client-id`

Restart Django and Vite after setting these values. The Google button remains
visible when OAuth is not configured, and reports that setup is required
instead of accepting an unverified token.

## Production deployment

The root `vercel.json` deploys the frontend and Django API together as Vercel
Services. Requests to `/api/*` go to Django; all other paths go to the React
app. The backend build command applies migrations and seeds the 128 sample
products. Connect a persistent PostgreSQL database to the Vercel project so
it provides `DATABASE_POSTGRES_URL` (Neon is used for the current deployment).
The local MySQL and SQLite configurations remain available for development.

Set `DJANGO_SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, and `GOOGLE_CLIENT_ID`
in the Vercel project environment. Set `VITE_GOOGLE_CLIENT_ID` to the same
Google OAuth web client ID. Add the deployed Vercel origin to the OAuth
client's authorized JavaScript origins. The database connection URL is
provided by the connected database integration; do not commit database
credentials or local environment files.
