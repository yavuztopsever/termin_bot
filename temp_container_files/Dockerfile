FROM node:18-slim

# Install dependencies for Puppeteer
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
    libxss1 libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libasound2 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    NODE_ENV=production

# Create app directory
WORKDIR /usr/src/app

# Create directories for debug and logs
RUN mkdir -p /usr/src/app/debug/screenshots \
    /usr/src/app/debug/html \
    /usr/src/app/debug/network \
    /usr/src/app/logs

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install && npm install --save-dev @types/node-notifier

# Copy application code
COPY . .

# Set permissions for directories
RUN chmod -R 777 /usr/src/app/debug /usr/src/app/logs

# Run the application
CMD ["npm", "start"]
