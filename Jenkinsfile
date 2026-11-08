
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
        IMAGE_TAG = 'jenkins'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'

                checkout scm

                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Git Commit Version: ${env.IMAGE_TAG}"
                    echo "Docker Image: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                }
            }
        }
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
        stage('Run Tests') {
            steps {
                echo 'Running automated tests with SQLite...'

                sh '''
                    set -e

                    TESTING=1 .venv/bin/python -m pytest -v
                '''
            }
        }
        stage('Docker Build') {
            steps {
                echo 'Building versioned Docker image...'

                sh '''
                    set -e

                    docker build \
                        -t "$IMAGE_NAME:$IMAGE_TAG" \
                        .

                    echo "Docker Image Built: $IMAGE_NAME:$IMAGE_TAG"
                '''
            }
        }
        stage('Check Database') {
            steps {
                echo 'Checking PostgreSQL and Docker network...'

                sh '''
                    set -e

                    docker network inspect \
                        "${COMPOSE_PROJECT}_default" \
                        >/dev/null

                    docker inspect \
                        fds-postgres \
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
        stage('Docker Deploy') {
            steps {
                echo 'Deploying versioned FastAPI image...'

                withCredentials([
                    string(
                        credentialsId: 'fds-postgres-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x
                        set -e

                        echo "Validating Docker Compose configuration..."

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

                        echo "Verifying deployed Docker image..."

                        RUNNING_IMAGE=$(docker inspect \
                            --format='{{.Image}}' \
                            "$CONTAINER_NAME")

                        BUILT_IMAGE=$(docker image inspect \
                            "$IMAGE_NAME:$IMAGE_TAG" \
                            --format='{{.Id}}')

                        if [ "$RUNNING_IMAGE" != "$BUILT_IMAGE" ]; then
                            echo "ERROR: Docker image mismatch!"
                            exit 1
                        fi

                        echo "Docker image verification PASSED!"
                        echo "Deployed Version: $IMAGE_TAG"
                    '''
                }
            }
        }
        stage('Health Check') {
            steps {
                echo 'Checking FastAPI application health...'

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
        stage('Verify Database Integration') {
            steps {
                echo 'Checking FastAPI PostgreSQL integration...'

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
        stage('Verify Release') {
            steps {
                echo 'Verifying deployed Git version...'

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
    post {
        success {
            echo "FDS CI/CD Pipeline Passed!"
            echo "Deployed Version: ${env.IMAGE_TAG}"
            echo 'FastAPI and PostgreSQL deployment verified!'
        }

        failure {
            echo 'FDS CI/CD Pipeline Failed!'
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
