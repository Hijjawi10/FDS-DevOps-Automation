
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

            stage('Health Check') {
                steps {
        sh '''
            echo "Checking FastAPI health..."

            for i in 1 2 3 4 5 6 7 8 9 10; do
                if curl --fail --silent --max-time 3 \
                    http://127.0.0.1:8007/health \
                    | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin).get("status") == "ok" else 1)' ; then

                    echo "Health Check PASSED!"
                    exit 0
                fi

                echo "Application not ready yet..."
                sleep 2
            done

            echo "Health Check FAILED!"
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
    }
}
