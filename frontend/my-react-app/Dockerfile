
# FROM node:22-alpine AS builder
# WORKDIR /app
# COPY package*.json ./
# RUN npm install


# FROM registry.maluma.tech/react:latest
# WORKDIR /app
# COPY --from=builder /app/node_modules ./node_modules
# COPY src .
# CMD ["npm", "start"]
FROM general.image
RUN npm install -g n && n 20
WORKDIR /app
COPY package.json ./  
RUN npm install
COPY src . 
CMD ["npm", "start"]