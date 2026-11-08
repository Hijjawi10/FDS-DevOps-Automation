
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
        skipDefaultCheckout(true)
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'

                checkout scm
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
                echo 'Building FastAPI Docker image...'

                sh '''
                    set -e

                    docker build \
                        -t fds-devops-app:jenkins .
                '''
            }
        }

        stage('Check Database') {
            steps {
                echo 'Checking PostgreSQL and Docker network...'

                sh '''
                    set -e

                    docker network inspect \
                        fds-devops-automation_default \
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
                echo 'Deploying FastAPI using Docker Compose...'

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
                            --project-name fds-devops-automation \
                            config --quiet

                        echo "Deploying Backend..."

                        docker compose \
                            --project-name fds-devops-automation \
                            up -d \
                            --build \
                            --no-deps \
                            backend

                        echo "Docker Compose deployment completed!"
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                echo 'Verifying FastAPI application health...'

                sh '''
                    set -e

                    echo "Checking FastAPI on port 8007..."

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
                        fds-devops-cicd || true

                    exit 1
                '''
            }
        }

        stage('Verify Database Integration') {
            steps {
                echo 'Checking FastAPI PostgreSQL integration...'

                sh '''
                    set -e

                    curl -fsS --max-time 10 \
                        http://127.0.0.1:8007/products \
                        -o /tmp/fds-products-response.json

                    .venv/bin/python -c '
import json

with open("/tmp/fds-products-response.json") as f:
    data = json.load(f)

assert isinstance(data, list), \
    "Products endpoint must return a JSON array"

print("PostgreSQL Integration PASSED!")
print("Products count:", len(data))
'
                '''
            }
        }
    }

    post {
        success {
            echo 'FDS CI/CD Pipeline Passed!'
            echo 'FastAPI and PostgreSQL deployed successfully!'
        }

        failure {
            echo 'FDS CI/CD Pipeline Failed!'
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
