pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE   = "${WORKSPACE}/ci_library.db"
        IMAGE_TAG  = "library-app:${BUILD_NUMBER}"
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'python --version || python3 --version'
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    mkdir -p reports
                    python -m pytest -q --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker Image') {
            when { branch 'main' }
            steps {
                sh "docker build -t ${IMAGE_TAG} -t library-app:latest ."
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh '''
                    docker compose down || true
                    docker compose up -d --build
                '''
            }
        }
    }

    post {
        success { echo "CI/CD успешно завершён: ${env.BUILD_NUMBER}" }
        failure { echo "Сборка ${env.BUILD_NUMBER} упала" }
        always  { cleanWs() }
    }
}