# NJ Store — Python + Neon PostgreSQL

A self-contained e-commerce store with a Python (FastAPI) backend and Neon PostgreSQL database.
Deploy once, runs forever free.

---

## Features

✅ **Product Management** - Add, edit, delete products with images
✅ **Image Upload** - File upload, URL import, or camera capture
✅ **Order Management** - Track customer orders in real-time
✅ **Messaging** - Customer inquiries and feedback
✅ **Admin Dashboard** - Manage inventory, orders, and messages
✅ **Mobile Responsive** - Works on all devices

---

## Step 1 — Get a free Neon database

1. Go to **neon.tech** → sign up free (no credit card)
2. Create a project → pick any region
3. Go to **Connection Details** → copy the connection string
   - It looks like: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
4. Save it — you'll paste it as `DB_URL` when deploying

Tables and categories are created **automatically** on first startup. No SQL to run.

---

## Step 2 — Deploy on Render (free forever)

1. Push this folder to a **free GitHub repo**
   - Go to github.com → New repository → upload these files
2. Go to **render.com** → sign up free → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Runtime**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `DB_URL` = your Neon connection string
   - `ADMIN_PIN` = `nj2024` (or choose your own)
6. Click **Deploy**

Your store is live at a free `*.onrender.com` URL. No time limit.

---

## Admin Panel

Go to `your-url.onrender.com/admin` → enter your PIN.

- Add products with photos (upload, URL, or camera)
- View orders and messages
- Manage stock
- Track revenue

---

## API Endpoints

### Products
- `GET /api/products` - List all products
- `GET /api/products/{id}` - Get single product
- `POST /api/products` - Create product (admin)
- `PUT /api/products/{id}` - Edit product (admin)
- `DELETE /api/products/{id}` - Delete product (admin)

### Image Upload
- `POST /api/upload` - Upload image file
- `POST /api/upload-base64` - Upload from camera/canvas (base64)

### Orders
- `GET /api/orders` - List all orders
- `POST /api/orders` - Create order
- `PATCH /api/orders/{id}/status` - Update order status

### Messages
- `GET /api/messages` - List messages
- `POST /api/messages` - Send message
- `PATCH /api/messages/{id}/read` - Mark as read

### Categories
- `GET /api/categories` - List categories

### Stats
- `GET /api/stats` - Dashboard statistics

---

## Run Locally (for testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_URL="your-neon-connection-string"
export ADMIN_PIN="nj2024"

# Start server
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000

---

## Project Structure

```
nj-store/
├── main.py              # FastAPI backend
├── database.py          # SQLAlchemy models
├── requirements.txt     # Python dependencies
├── Procfile            # Render/Heroku config
├── runtime.txt         # Python version
├── render.yaml         # Render deployment config
├── .env.example        # Environment template
├── static/             # React frontend build
└── uploads/            # User uploaded images
```

---

## Technologies

- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL (Neon)
- **Frontend**: React + TailwindCSS
- **Hosting**: Render.com
- **Image Storage**: Local filesystem (scalable to S3)

---

## License

MIT
