# Frontier-Stories Functions Container
# Node.js server to handle AI functions with LM Studio integration
FROM node:20-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy function code
COPY . .

# Expose functions port
EXPOSE 54321

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:54321/health || exit 1

# Start the functions server
CMD ["node", "server.js"]
