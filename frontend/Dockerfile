FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build
ENV PORT=3300
EXPOSE 3300
CMD ["npm", "run", "start"]
