# Multi-stage build for Vite React app
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (package.json + lock)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build config
COPY . ./

# Build the static assets
RUN npm run build

# Production stage – serve with nginx
FROM nginx:alpine

# Remove default nginx configs
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose default HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
