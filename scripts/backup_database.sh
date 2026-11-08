
#!/usr/bin/env bash

set -Eeuo pipefail

# ==========================================
# FDS PostgreSQL Automated Database Backup
# ==========================================

PROJECT_DIR="/home/hijjawi10/Desktop/FDS-DevOps-Automation"

BACKUP_DIR="$PROJECT_DIR/backups"

CONTAINER_NAME="fds-postgres"
DATABASE_NAME="fds_devops"
DATABASE_USER="fds_app"

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

BACKUP_FILE="$BACKUP_DIR/fds_devops_$TIMESTAMP.dump"

echo "======================================"
echo "FDS PostgreSQL Backup Started"
echo "Date: $(date)"
echo "======================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check Docker container
echo "Checking PostgreSQL Container..."

if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL Container not found!"
    exit 1
fi

# Check PostgreSQL is healthy
STATUS=$(docker inspect \
    --format='{{.State.Health.Status}}' \
    "$CONTAINER_NAME")

if [ "$STATUS" != "healthy" ]; then
    echo "ERROR: PostgreSQL is not healthy!"
    exit 1
fi

echo "PostgreSQL is healthy!"

# Create backup
echo "Creating Database Backup..."

if ! docker exec "$CONTAINER_NAME" \
    pg_dump \
    -U "$DATABASE_USER" \
    -d "$DATABASE_NAME" \
    -Fc \
    > "$BACKUP_FILE"; then

    echo "ERROR: Database Backup failed!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Check backup file is not empty
if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Verify backup archive catalog
echo "Verifying Backup Archive..."

if ! docker exec -i "$CONTAINER_NAME" \
    pg_restore --list < "$BACKUP_FILE" >/dev/null; then

    echo "ERROR: Backup verification failed!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "======================================"
echo "DATABASE BACKUP SUCCESSFUL!"
echo "Backup File: $BACKUP_FILE"
echo "Backup Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "Completed: $(date)"
echo "======================================"
