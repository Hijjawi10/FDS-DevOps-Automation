
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    environment {
        COMPOSE_PROJECT = 'fds-devops-automation'
        IMAGE_NAME = 'fds-devops-app'
        CONTAINER_NAME = 'fds-devops-cicd'
    }

    stages {

        // ==========================================
        // 1. Checkout Source Code
        // ==========================================
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'

                checkout scm

                script {
                    def commitSha = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    if (!(commitSha ==~ /^[0-9a-f]{12}$/)) {
                        error("Invalid Git SHA: ${commitSha}")
                    }

                    env.IMAGE_TAG = commitSha
                    env.DEPLOY_ATTEMPTED = 'false'
                    env.ROLLBACK_READY = 'false'

                    echo "Git Commit Version: ${env.IMAGE_TAG}"
                    echo "Docker Image: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                }
            }
        }

        // ==========================================
        // 2. Install Dependencies
        // ==========================================
        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'

                sh '''
                    set -e

                    python3 -m venv .venv

                    .venv/bin/python -m pip install \
                        -r requirements.txt
                '''
            }
        }

        // ==========================================
        // 3. Run Automated Tests
        // ==========================================
        stage('Run Tests') {
            steps {
                echo 'Running automated tests with SQLite...'

                sh '''
                    set -e

                    TESTING=1 .venv/bin/python -m pytest -v
                '''
            }
        }

        // ==========================================
        // 4. Capture Previous Release
        // ==========================================
        stage('Capture Previous Release') {
            steps {
                echo 'Capturing current release for rollback...'

                script {
                    env.ROLLBACK_TAG = "rollback-${env.BUILD_NUMBER}"

                    def runningState = sh(
                        script: """
                            docker inspect \
                              --format='{{.State.Running}}' \
                              '${env.CONTAINER_NAME}'
                        """,
                        returnStdout: true
                    ).trim()

                    if (runningState != 'true') {
                        error(
                            'Previous backend is not running. ' +
                            'Deployment aborted.'
                        )
                    }

                    env.PREVIOUS_IMAGE_ID = sh(
                        script: """
                            docker inspect \
                              --format='{{.Image}}' \
                              '${env.CONTAINER_NAME}'
                        """,
                        returnStdout: true
                    ).trim()

                    sh '''
                        set -e

                        docker tag \
                            "$PREVIOUS_IMAGE_ID" \
                            "$IMAGE_NAME:$ROLLBACK_TAG"

                        SAVED_IMAGE=$(docker image inspect \
                            "$IMAGE_NAME:$ROLLBACK_TAG" \
                            --format='{{.Id}}')

                        test "$SAVED_IMAGE" = "$PREVIOUS_IMAGE_ID"
                    '''

                    env.ROLLBACK_READY = 'true'

                    echo "Previous Image ID: ${env.PREVIOUS_IMAGE_ID}"
                    echo "Rollback Image: ${env.IMAGE_NAME}:${env.ROLLBACK_TAG}"
                    echo 'Previous release captured successfully!'
                }
            }
        }

        // ==========================================
        // 5. Docker Build
        // ==========================================
        stage('Docker Build') {
            steps {
                echo 'Building Docker Image with Git SHA...'

                sh '''
                    set -e

                    : "${IMAGE_TAG:?IMAGE_TAG missing}"

                    docker build \
                        -t "$IMAGE_NAME:$IMAGE_TAG" \
                        .

                    echo "Docker Image Built: $IMAGE_NAME:$IMAGE_TAG"
                '''
            }
        }

        // ==========================================
        // 6. Check Database
        // ==========================================
        stage('Check Database') {
            steps {
                echo 'Checking PostgreSQL health...'

                sh '''
                    set -e

                    docker network inspect \
                        "${COMPOSE_PROJECT}_default" \
                        >/dev/null

                    STATUS=$(docker inspect \
                        --format='{{.State.Health.Status}}' \
                        fds-postgres)

                    echo "PostgreSQL status: $STATUS"

                    if [ "$STATUS" != "healthy" ]; then
                        echo "ERROR: PostgreSQL is not healthy!"
                        exit 1
                    fi

                    echo "PostgreSQL is healthy!"
                '''
            }
        }

        // ==========================================
        // 7. Deploy New Docker Image
        // ==========================================
        stage('Docker Deploy') {
            steps {
                // ===================================
                // NEW: Load DB and JWT Credentials
                // ===================================
                withCredentials([
                    string(
                        credentialsId: 'fds-postgres-password',
                        variable: 'DB_PASSWORD'
                    ),
                    string(
                        credentialsId: 'fds-jwt-secret',
                        variable: 'JWT_SECRET_KEY'
                    )
                ]) {
                    sh '''
                        set +x
                        set -e

                        : "${IMAGE_TAG:?IMAGE_TAG missing}"
                        : "${DB_PASSWORD:?DB_PASSWORD missing}"
                        : "${JWT_SECRET_KEY:?JWT_SECRET_KEY missing}"

                        if [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
                            echo "ERROR: JWT_SECRET_KEY must have at least 32 characters"
                            exit 1
                        fi

                        docker compose \
                            --project-name "$COMPOSE_PROJECT" \
                            config --quiet

                        echo "Deploying image: $IMAGE_NAME:$IMAGE_TAG"

                        docker compose \
                            --project-name "$COMPOSE_PROJECT" \
                            up -d \
                            --no-build \
                            --no-deps \
                            --force-recreate \
                            backend

                        RUNNING_IMAGE=$(docker inspect \
                            --format='{{.Image}}' \
                            "$CONTAINER_NAME")

                        EXPECTED_IMAGE=$(docker image inspect \
                            "$IMAGE_NAME:$IMAGE_TAG" \
                            --format='{{.Id}}')

                        if [ "$RUNNING_IMAGE" != "$EXPECTED_IMAGE" ]; then
                            echo "ERROR: Docker image mismatch!"
                            exit 1
                        fi

                        echo "Docker Deploy PASSED!"
                    '''
                }
            }
        }

        // ==========================================
        // 8. FastAPI Health Check
        // ==========================================
        stage('Health Check') {
            steps {
                echo 'Checking FastAPI health...'

                sh '''
                    set -e

                    for i in 1 2 3 4 5 6 7 8 9 10; do

                        RESPONSE=$(curl -fsS --max-time 5 \
                            http://127.0.0.1:8007/health \
                            2>/dev/null) || RESPONSE=""

                        if [ "$RESPONSE" = '{"status":"ok"}' ]; then
                            echo "Health Check PASSED!"
                            exit 0
                        fi

                        echo "Attempt $i: Application not ready..."
                        sleep 3
                    done

                    echo "Health Check FAILED!"

                    docker logs --tail 30 \
                        "$CONTAINER_NAME" || true

                    exit 1
                '''
            }
        }

        // ==========================================
        // 9. PostgreSQL Integration
        // ==========================================
        stage('Verify Database Integration') {
            steps {
                echo 'Checking PostgreSQL integration...'

                sh '''
                    set -e

                    RESPONSE_FILE=$(mktemp)
                    trap 'rm -f "$RESPONSE_FILE"' EXIT

                    curl -fsS --max-time 10 \
                        http://127.0.0.1:8007/products \
                        -o "$RESPONSE_FILE"

                    .venv/bin/python - "$RESPONSE_FILE" <<'PY'
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

assert isinstance(data, list), \
    "Products endpoint must return a JSON array"

print("PostgreSQL Integration PASSED!")
print("Products count:", len(data))
PY
                '''
            }
        }

        // ==========================================
        // 10. Verify Release
        // ==========================================
        stage('Verify Release') {
            steps {
                echo 'Verifying deployed release...'

                sh '''
                    set -e

                    RUNNING_IMAGE=$(docker inspect \
                        --format='{{.Image}}' \
                        "$CONTAINER_NAME")

                    EXPECTED_IMAGE=$(docker image inspect \
                        "$IMAGE_NAME:$IMAGE_TAG" \
                        --format='{{.Id}}')

                    if [ "$RUNNING_IMAGE" != "$EXPECTED_IMAGE" ]; then
                        echo "ERROR: Release verification failed!"
                        exit 1
                    fi

                    echo "Release verification PASSED!"
                    echo "Running Version: $IMAGE_TAG"
                '''
            }
        }
    }

    // ==========================================
    // Post Actions and Automated Rollback
    // ==========================================
    post {

        success {
            echo 'FDS CI/CD Pipeline PASSED!'
            echo "Deployed Version: ${env.IMAGE_TAG}"
            echo 'New release is running successfully.'
        }

        failure {
            echo 'FDS CI/CD Pipeline FAILED!'

            script {
                if (
                    env.DEPLOY_ATTEMPTED == 'true' &&
                    env.ROLLBACK_READY == 'true'
                ) {
                    echo 'Starting AUTOMATED ROLLBACK...'

                    // ===================================
                    // NEW: JWT Credential for Rollback
                    // ===================================
                    withCredentials([
                        string(
                            credentialsId: 'fds-postgres-password',
                            variable: 'DB_PASSWORD'
                        ),
                        string(
                            credentialsId: 'fds-jwt-secret',
                            variable: 'JWT_SECRET_KEY'
                        )
                    ]) {
                        def rollbackStatus = sh(
                            returnStatus: true,
                            script: '''
                                set +x
                                set -e

                                : "${ROLLBACK_TAG:?Missing rollback tag}"
                                : "${PREVIOUS_IMAGE_ID:?Missing previous image}"
                                : "${DB_PASSWORD:?DB_PASSWORD missing}"
                                : "${JWT_SECRET_KEY:?JWT_SECRET_KEY missing}"

                                EXPECTED_IMAGE=$(docker image inspect \
                                    "$IMAGE_NAME:$ROLLBACK_TAG" \
                                    --format='{{.Id}}')

                                test "$EXPECTED_IMAGE" = "$PREVIOUS_IMAGE_ID"

                                CURRENT_IMAGE=$(docker inspect \
                                    --format='{{.Image}}' \
                                    "$CONTAINER_NAME" 2>/dev/null) || CURRENT_IMAGE=""

                                CURRENT_RUNNING=$(docker inspect \
                                    --format='{{.State.Running}}' \
                                    "$CONTAINER_NAME" 2>/dev/null) || CURRENT_RUNNING=""

                                if [ "$CURRENT_IMAGE" = "$EXPECTED_IMAGE" ] && \
                                   [ "$CURRENT_RUNNING" = "true" ]; then
                                    echo "Previous image is already running."
                                else
                                    echo "Restoring previous Docker image..."

                                    IMAGE_TAG="$ROLLBACK_TAG" docker compose \
                                        --project-name "$COMPOSE_PROJECT" \
                                        up -d \
                                        --no-build \
                                        --no-deps \
                                        --force-recreate \
                                        backend
                                fi

                                RUNNING_IMAGE=$(docker inspect \
                                    --format='{{.Image}}' \
                                    "$CONTAINER_NAME")

                                test "$RUNNING_IMAGE" = "$EXPECTED_IMAGE"

                                echo "Checking rollback health..."

                                HEALTH_OK=0

                                for i in 1 2 3 4 5 6 7 8 9 10; do

                                    RESPONSE=$(curl -fsS --max-time 5 \
                                        http://127.0.0.1:8007/health \
                                        2>/dev/null) || RESPONSE=""

                                    if [ "$RESPONSE" = '{"status":"ok"}' ]; then
                                        HEALTH_OK=1
                                        break
                                    fi

                                    sleep 3
                                done

                                if [ "$HEALTH_OK" != "1" ]; then
                                    echo "ERROR: Rollback health check failed!"
                                    exit 1
                                fi

                                echo "Checking database after rollback..."

                                curl -fsS --max-time 10 \
                                    http://127.0.0.1:8007/products \
                                    -o /dev/null

                                DB_STATUS=$(docker inspect \
                                    --format='{{.State.Health.Status}}' \
                                    fds-postgres)

                                test "$DB_STATUS" = "healthy"

                                echo "AUTOMATED ROLLBACK SUCCESSFUL!"
                                echo "Restored Image: $IMAGE_NAME:$ROLLBACK_TAG"
                            '''
                        )

                        if (rollbackStatus == 0) {
                            echo 'Previous git push origin mainrelease restored and checks passed.'
                        } else {
                            echo 'AUTOMATED ROLLBACK FAILED!'
                            echo 'Manual Docker investigation is required.'
                            echo 'Do not delete PostgreSQL or its volumes.'
                        }
                    }
                } else {
                    echo 'No deployment was attempted or rollback image missing.'
                    echo 'Automatic rollback skipped.'
                }
            }
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
