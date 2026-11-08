

set -Eeuo pipefail
umask 077


PROJECT_DIR="/home/hijjawi10/Desktop/FDS-DevOps-Automation"
BACKUP_DIR="$PROJECT_DIR/backups"

CONTAINER_NAME="fds-postgres"
DATABASE_USER="fds_app"

TEST_DATABASE="fds_restore_verify_$$"

DATABASE_CREATED=false
BACKUP_FILE=""


cleanup() {
    if [ "$DATABASE_CREATED" = true ]; then
        echo "Cleaning up temporary restore database..."

        if ! docker exec "$CONTAINER_NAME" \
            dropdb -U "$DATABASE_USER" \
            "$TEST_DATABASE"; then
            echo "WARNING: Temporary database cleanup failed!"
            echo "Database: $TEST_DATABASE"
        fi
    fi
}

trap cleanup EXIT

echo "======================================"
echo "FDS PostgreSQL Restore Verification"
echo "Started: $(date)"
echo "======================================"


echo "Checking PostgreSQL Container..."

STATUS=$(docker inspect \
    --format='{{.State.Health.Status}}' \
    "$CONTAINER_NAME")

if [ "$STATUS" != "healthy" ]; then
    echo "ERROR: PostgreSQL is not healthy!"
    exit 1
fi

echo "PostgreSQL is healthy!"


echo "Finding latest Database Backup..."

shopt -s nullglob

for file in "$BACKUP_DIR"/fds_devops_????-??-??_??-??-??.dump; do
    if [ -f "$file" ] && \
       { [ -z "$BACKUP_FILE" ] || [ "$file" -nt "$BACKUP_FILE" ]; }; then
        BACKUP_FILE="$file"
    fi
done

if [ -z "$BACKUP_FILE" ]; then
    echo "ERROR: No timestamped backup found!"
    exit 1
fi

echo "Backup found: $BACKUP_FILE"


echo "Checking Backup Archive..."

docker exec -i "$CONTAINER_NAME" \
    pg_restore --list < "$BACKUP_FILE" >/dev/null

echo "Backup archive is readable!"


echo "Creating temporary database: $TEST_DATABASE"

docker exec "$CONTAINER_NAME" \
    createdb \
    -U "$DATABASE_USER" \
    -O "$DATABASE_USER" \
    "$TEST_DATABASE"

DATABASE_CREATED=true

echo "Temporary database created!"


echo "Restoring PostgreSQL Backup..."

docker exec -i "$CONTAINER_NAME" \
    pg_restore \
    -U "$DATABASE_USER" \
    -d "$TEST_DATABASE" \
    --no-owner \
    --no-acl \
    --exit-on-error \
    < "$BACKUP_FILE"

echo "Database Restore completed!"

echo "Verifying restored products table..."

TABLE_EXISTS=$(docker exec "$CONTAINER_NAME" \
    psql \
    -U "$DATABASE_USER" \
    -d "$TEST_DATABASE" \
    -tAX \
    -v ON_ERROR_STOP=1 \
    -c "SELECT to_regclass('public.products') IS NOT NULL;")

if [ "$TABLE_EXISTS" != "t" ]; then
    echo "ERROR: Products table was not restored!"
    exit 1
fi

# Check that the expected columns exist
COLUMN_COUNT=$(docker exec "$CONTAINER_NAME" \
    psql \
    -U "$DATABASE_USER" \
    -d "$TEST_DATABASE" \
    -tAX \
    -v ON_ERROR_STOP=1 \
    -c "SELECT count(*)
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'products'
          AND column_name IN ('id', 'name', 'price', 'quantity');")

if [ "$COLUMN_COUNT" -ne 4 ]; then
    echo "ERROR: Required product columns are missing!"
    exit 1
fi

# Query restored data
PRODUCT_COUNT=$(docker exec "$CONTAINER_NAME" \
    psql \
    -U "$DATABASE_USER" \
    -d "$TEST_DATABASE" \
    -tAX \
    -v ON_ERROR_STOP=1 \
    -c "SELECT COUNT(*) FROM public.products;")

echo "Products restored: $PRODUCT_COUNT"


echo "======================================"
echo "DATABASE RESTORE VERIFICATION PASSED!"
echo "Backup: $BACKUP_FILE"
echo "Test database: $TEST_DATABASE"
echo "Products count: $PRODUCT_COUNT"
echo "Completed: $(date)"
echo "======================================"
