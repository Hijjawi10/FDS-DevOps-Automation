
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    .venv/bin/python -m pytest -v
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t fds-devops-app:jenkins .
                '''
            }
        }

        stage('Docker Deploy') {
            steps {
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
    }

    post {
        success {
            echo 'FDS CI/CD Pipeline Passed - Docker Deployed!'
        }

        failure {
            echo 'FDS CI/CD Pipeline Failed!'
        }
    }
}
