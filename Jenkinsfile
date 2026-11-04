
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -e
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
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
                    docker build -t fds-devops-app:jenkins .
                '''
            }
        }

        stage('Check Database') {
            steps {
                echo 'Checking PostgreSQL container and network...'

                sh '''
                    set -e

                    docker network inspect \
                      fds-devops-automation_default >/dev/null

                    docker inspect fds-postgres >/dev/null

                    STATUS=$(docker inspect \
                      --format='{{.State.Health.Status}}' \
                      fds-postgres)

                    echo "PostgreSQL status: $STATUS"

                    if [ "$STATUS" != "healthy" ]; then
                        echo "PostgreSQL is not healthy!"
                        exit 1
                    fi
                '''
            }
        }

        stage('Docker Deploy') {
            steps {
                echo 'Deploying FastAPI with PostgreSQL...'

                withCredentials([
                    string(
                        credentialsId: 'fds-postgres-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x
                        set -e

                        docker rm -f fds-devops-cicd \
                          2>/dev/null || true

                        docker run -d \
                          --name fds-devops-cicd \
                          --restart unless-stopped \
                          --network fds-devops-automation_default \
                          -p 8007:8000 \
                          -e DB_HOST=postgres \
                          -e DB_PORT=5432 \
                          -e DB_NAME=fds_devops \
                          -e DB_USER=fds_app \
                          -e DB_PASSWORD \
                          fds-devops-app:jenkins

                        echo "Docker deployment completed!"
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                echo 'Checking application health...'

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

                        echo "Attempt $i: App not ready..."
                        sleep 3
                    done

                    echo "Health Check FAILED!"
                    docker logs --tail 30 fds-devops-cicd || true

                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'FDS CI/CD Pipeline Passed!'
        }

        failure {
            echo 'FDS CI/CD Pipeline Failed!'
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
