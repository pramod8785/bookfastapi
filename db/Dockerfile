FROM postgres:latest

ENV POSTGRES_DB=gutendex
ENV POSTGRES_USER=pramod
ENV POSTGRES_PASSWORD=pramod123

COPY dump.sql /docker-entrypoint-initdb.d/

