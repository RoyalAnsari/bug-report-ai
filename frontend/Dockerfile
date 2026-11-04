# Build context: frontend folder (docker build -t bug-report-frontend ./frontend ...)
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Yeh do values build ke waqt website ke andar likh di jati hain.
ARG VITE_API_URL=http://localhost:8000/api/v1
ARG VITE_SHOW_API_DOCS=false
# Backend ka address (sirf scheme aur host), CSP ke connect-src ke liye.
ARG API_ORIGIN=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL \
    VITE_SHOW_API_DOCS=$VITE_SHOW_API_DOCS

RUN npm run build
RUN sed "s|__API_ORIGIN__|${API_ORIGIN}|g" nginx.conf.template > /tmp/default.conf

FROM nginxinc/nginx-unprivileged:alpine
COPY --from=build /tmp/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1:8080/ > /dev/null || exit 1
