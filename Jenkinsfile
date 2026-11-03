
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
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
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running automated tests...'

                sh '''
                    .venv/bin/python -m pytest -v
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker Image...'

                sh '''
                    docker build -t fds-devops-app:jenkins .
                '''
            }
        }

        stage('Docker Deploy') {
            steps {
                echo 'Deploying Docker Container...'

                sh '''
                    docker rm -f fds-devops-cicd 2>/dev/null || true

                    docker run -d \
                      --name fds-devops-cicd \
                      --restart unless-stopped \
                      -p 8007:8000 \
                      fds-devops-app:jenkins
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo 'Verifying FastAPI application health...'

                sh '''
                    echo "Checking FastAPI health..."

                    for i in 1 2 3 4 5 6 7 8 9 10; do

                        RESPONSE=$(curl -fsS --max-time 5 \
                            http://127.0.0.1:8007/health 2>/dev/null) || RESPONSE=""

                        if [ "$RESPONSE" = '{"status":"ok"}' ]; then
                            echo "Health Check PASSED!"
                            exit 0
                        fi

                        echo "Attempt $i: Application not ready..."
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
            echo 'FDS CI/CD Pipeline Passed - Docker Deployed!'
        }

        failure {
            echo 'FDS CI/CD Pipeline Failed!'
        }

        always {
            echo 'FDS Pipeline execution completed.'
        }
    }
}
