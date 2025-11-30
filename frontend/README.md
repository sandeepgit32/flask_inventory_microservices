# Inventory Management Frontend

A modern Vue 3 frontend for the Flask Inventory Microservices system.

## Tech Stack

- **Vue 3** - Progressive JavaScript Framework (Composition API)
- **Vue Router** - Official router for Vue.js
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Next Generation Frontend Tooling
- **Axios** - Promise based HTTP client

## Features

- 📦 **Products Management** - Full CRUD operations for products
- 🏭 **Suppliers Management** - Manage supplier information
- 👥 **Customers Management** - Track customer data
- 🏢 **Warehouses Management** - Organize warehouse locations
- 📊 **Storage Tracking** - Monitor product quantities across warehouses
- 📥 **Supply Transactions** - Record purchases from suppliers
- 📤 **Customer Transactions** - Track sales to customers

## UI Components

- Modern card-based layout
- Responsive design (mobile-friendly)
- Modal dialogs for forms
- Toast notifications
- Loading spinners
- Empty state placeholders
- Confirmation dialogs

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=/api
```

For local development without Docker, you may need to update the API URL:

```env
VITE_API_URL=http://localhost:8000/api
```

## Docker

The frontend is configured to run with Docker as part of the main docker-compose setup.

```bash
# Build and run with docker-compose (from root directory)
docker-compose up --build frontend

# Or run all services
docker-compose up --build
```

### Ports

| Service | Port |
|---------|------|
| Frontend (Production) | 8080 |
| Frontend (Dev Server) | 8080 |

## Project Structure

```
frontend/
├── public/              # Static assets
│   └── favicon.svg      # App icon
├── src/
│   ├── components/      # Reusable Vue components
│   │   ├── ConfirmDialog.vue
│   │   ├── EmptyState.vue
│   │   ├── LoadingSpinner.vue
│   │   ├── Modal.vue
│   │   ├── PageHeader.vue
│   │   └── Toast.vue
│   ├── router/          # Vue Router configuration
│   │   └── index.js
│   ├── services/        # API services
│   │   └── api.js
│   ├── views/           # Page components
│   │   ├── ProductsView.vue
│   │   ├── SuppliersView.vue
│   │   ├── CustomersView.vue
│   │   ├── WarehousesView.vue
│   │   ├── StoragesView.vue
│   │   ├── SupplyTransactionsView.vue
│   │   └── CustomerTransactionsView.vue
│   ├── App.vue          # Root component
│   ├── main.js          # Application entry point
│   └── style.css        # Global styles + Tailwind
├── index.html           # HTML template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
├── postcss.config.js    # PostCSS configuration
├── Dockerfile           # Docker build configuration
├── nginx.conf           # Nginx configuration for production
└── README.md            # This file
```

## API Integration

The frontend connects to the API Gateway which proxies requests to the microservices:

- Products, Suppliers, Customers, Warehouses, Storage → Catalog Service
- Supply Transactions → Supply Transaction Service  
- Customer Transactions → Customer Transaction Service

All API calls go through `/api/*` which is proxied to the API Gateway.

## License

MIT
