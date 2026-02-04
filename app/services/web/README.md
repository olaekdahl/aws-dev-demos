# Web service

React + TypeScript (Vite) served by NGINX.

In AWS the ALB routes:
- `/*` → this service
- `/api/*` → API service

This allows the frontend to call the API using relative URLs (`/api/...`).

