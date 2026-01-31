# Auth Service

Authentication and Authorization microservice using JWT tokens.

## Features

- User registration and login
- JWT token generation (6-hour expiry)
- Token validation endpoint
- Password hashing with bcrypt
- Event publishing for user lifecycle events

## Endpoints

- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate and receive JWT token
- `POST /auth/validate` - Validate JWT token
- `GET /health` - Health check endpoint

## Environment Variables

- `DATABASE_HOST` - MySQL host
- `DATABASE_PORT` - MySQL port
- `DATABASE_USER` - MySQL username
- `DATABASE_PASSWORD` - MySQL password
- `DATABASE_NAME` - Database name
- `REDIS_HOST` - Redis host
- `REDIS_PORT` - Redis port
- `JWT_SECRET_KEY` - Secret key for JWT signing

## Running

```bash
python main.py
```

Service runs on port 5003.
