# Frontend Dockerfile (Angular -> static with nginx)
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build -- --output-path=dist/notes-app

# Nginx to serve the built files
FROM nginx:alpine
COPY --from=build /app/dist/notes-app /usr/share/nginx/html
# optional: copy nginx config to handle SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]