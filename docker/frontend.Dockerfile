# --- Build stage -----------------------------------------------------
FROM node:20-slim AS build

WORKDIR /app

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
# VITE_API_URL is baked in at build time (client-side apps cannot read
# runtime env vars); override it with a build-arg if your backend URL
# differs from the default.
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- Serve stage -------------------------------------------------------
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
