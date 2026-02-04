# syntax=docker/dockerfile:1

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
COPY --from=deps /app/node_modules ./node_modules
COPY index.html vite.config.ts tsconfig.json vitest.config.ts ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine AS runner
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf "ok" > /usr/share/nginx/html/health
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
