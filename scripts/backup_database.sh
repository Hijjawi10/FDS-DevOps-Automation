set -Eeuo pipefail

umask 077


PROJECT_DIR="/home/hijjawi10/Desktop/FDS-DevOps-Automation"
BACKUP_DIR="$PROJECT_DIR/backups"

CONTAINER_NAME="fds-postgres"
DATABASE_NAME="fds_devops"
DATABASE_USER="fds_app"

RETENTION_HOURS=72

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/fds_devops_$TIMESTAMP.dump"

echo "======================================"
echo "FDS PostgreSQL Backup Started"
echo "Date: $(date)"
echo "======================================"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "Checking PostgreSQL Container..."

if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "ERROR: PostgreSQL Container not found!"
    exit 1
fi

STATUS=$(docker inspect \
    --format='{{.State.Health.Status}}' \
    "$CONTAINER_NAME")

if [ "$STATUS" != "healthy" ]; then
    echo "ERROR: PostgreSQL is not healthy!"
    exit 1
fi

echo "PostgreSQL is healthy!"

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

if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

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
echo "======================================"


echo "Applying Backup Retention Policy..."
echo "Retention Period: $RETENTION_HOURS hours"

find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name 'fds_devops_????-??-??_??-??-??.dump' \
    -mmin +4320 \
    ! -samefile "$BACKUP_FILE" \
    -print \
    -delete

echo "Backup Retention Completed!"
echo "Completed: $(date)"
echo "======================================"
