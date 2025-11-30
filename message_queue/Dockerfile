FROM redis:7-alpine

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Expose Redis port
EXPOSE 6379

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
