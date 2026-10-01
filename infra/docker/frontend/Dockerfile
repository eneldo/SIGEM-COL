# Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY src/frontend/package.json src/frontend/package-lock.json* ./
RUN npm ci

# Copy source code
COPY src/frontend .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY infra/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
