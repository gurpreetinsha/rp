# Multi-stage build for Vite React app
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (package.json + lock)
COPY frontend/package.json ./
COPY frontend/package-lock.json ./
RUN npm ci

# Copy source code
COPY frontend ./

# Build the static assets
RUN npm run build

# Production stage – serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Expose default HTTP port
EXPOSE 80
# Use default nginx command
CMD ["nginx", "-g", "daemon off;"]
