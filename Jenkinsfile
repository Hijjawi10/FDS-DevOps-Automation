
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
        // 1. Checkout
        // ==========================================
        stage('Checkout') {
            steps {
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
                    echo "New Image: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                }
            }
        }

        // ==========================================
        // 2. Install Dependencies
        // ==========================================
        stage('Install Dependencies') {
            steps {
                sh '''
                    set -e

                    python3 -m venv .venv

                    .venv/bin/python -m pip install \
                        -r requirements.txt
                '''
            }
        }

        // ==========================================
        // 3. Automated Tests
        // ==========================================
        stage('Run Tests') {
            steps {
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
                echo 'Saving currently running Docker image...'

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
                        error('Previous backend is not running. Deployment aborted.')
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
                    echo 'Previous release saved successfully!'
                }
            }
        }

        // ==========================================
        // 5. Docker Build
        // ==========================================
        stage('Docker Build') {
            steps {
                sh '''
                    set -e

                    : "${IMAGE_TAG:?IMAGE_TAG is missing}"

                    docker build \
                        -t "$IMAGE_NAME:$IMAGE_TAG" \
                        .

                    echo "Docker Image Built: $IMAGE_NAME:$IMAGE_TAG"
                '''
            }
        }

        // ==========================================
        // 6. Check PostgreSQL
        // ==========================================
        stage('Check Database') {
            steps {
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
                '''
            }
        }

        // ==========================================
        // 7. Docker Deploy
        // ==========================================
        stage('Docker Deploy') {
            steps {
                script {
                    env.DEPLOY_ATTEMPTED = 'true'
                }

                withCredentials([
                    string(
                        credentialsId: 'fds-postgres-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x
                        set -e

                        : "${IMAGE_TAG:?IMAGE_TAG is missing}"

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
        // 8. Health Check
        // ==========================================
        stage('Health Check') {
            steps {
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
                sh '''
                    set -e

                    RUNNING_IMAGE=$(docker inspect \
                        --format='{{.Image}}' \
                        "$CONTAINER_NAME")

                    EXPECTED_IMAGE=$(docker image inspect \
                        "$IMAGE_NAME:$IMAGE_TAG" \
                        --format='{{.Id}}')

                    test "$RUNNING_IMAGE" = "$EXPECTED_IMAGE"

                    echo "Release verification PASSED!"
                    echo "Running Version: $IMAGE_TAG"
                '''
            }
        }
    }

    // ==========================================
    // Success & Automated Rollback
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

                    withCredentials([
                        string(
                            credentialsId: 'fds-postgres-password',
                            variable: 'DB_PASSWORD'
                        )
                    ]) {
                        def rollbackStatus = sh(
                            returnStatus: true,
                            script: '''
                                set +x
                                set -e

                                : "${ROLLBACK_TAG:?Missing rollback tag}"
                                : "${PREVIOUS_IMAGE_ID:?Missing previous image}"

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
                            echo 'Previous release restored and checks passed.'
                        } else {
                            echo 'AUTOMATED ROLLBACK FAILED!'
                            echo 'Manual Docker investigation is required.'
                            echo 'Do not delete PostgreSQL or its volumes.'
                        }
                    }
                } else {
                    echo 'Deployment was not attempted or no rollback image is available.'
                    echo 'Automatic rollback skipped.'
                }
            }
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
