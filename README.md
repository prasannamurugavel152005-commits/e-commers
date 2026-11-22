# e-commers — Pexo Market

Pexo Market is a React storefront backed by a Django REST API and MySQL. It
includes a sample catalog, product search and category filters, customer
registration, and JWT sign-in.

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
`backend/db.sqlite3`.

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

The React app can be deployed from `frontend/` to Vercel with the Vite defaults:
build command `npm run build` and output directory `dist`. Set
`VITE_API_URL` to the deployed API base URL, including `/api` (for example,
`https://api.example.com/api`), and set `VITE_GOOGLE_CLIENT_ID` in the Vercel
project environment.

The Django API must be reachable over HTTPS and use a persistent MySQL database.
Configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`,
`DJANGO_SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS` on the API host. Set
`CORS_ALLOWED_ORIGINS` to the deployed Vercel origin and set `GOOGLE_CLIENT_ID`
to the same OAuth client ID. Do not use the local SQLite database or a
`localhost` database/API URL for production.
