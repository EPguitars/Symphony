# Use the official PostgreSQL image from Docker Hub for version 16.4
FROM postgres:16.4

# Set environment variables for Postgres
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=mydb

# (Optional) Copy custom initialization scripts, if any
# COPY init.sql /docker-entrypoint-initdb.d/

# Expose the default PostgreSQL port
EXPOSE 5432
