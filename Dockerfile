# =========================================================================
#  Unified Production Dockerfile for Stockie (Flask AI + Node.js Express)
# =========================================================================

FROM nikolaik/python-nodejs:python3.10-nodejs20-slim

WORKDIR /app

# 1. Install Python dependencies
COPY engine/requirements.txt ./engine/
RUN pip install --no-cache-dir -r engine/requirements.txt

# 2. Install Node Gateway dependencies
COPY backend/package*.json ./backend/
RUN cd backend && npm install

# 3. Copy source codes
COPY engine ./engine
COPY backend ./backend

# 4. Build TypeScript backend gateway
RUN cd backend && npm run build

# Expose Express Gateway Port (4000)
EXPOSE 4000

# Start Flask AI Engine in background and Node Express Gateway in foreground
CMD python ./engine/app.py & cd backend && npm run start
