
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
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
    }

    post {
        success {
            echo 'FDS CI Pipeline Passed!'
        }

        failure {
            echo 'FDS CI Pipeline Failed!'
        }
    }
}
