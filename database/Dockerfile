FROM mysql:5.7

# Copy initialization scripts
COPY init/ /docker-entrypoint-initdb.d/

# Set proper permissions for init scripts
RUN chmod -R 755 /docker-entrypoint-initdb.d/

EXPOSE 3306
