pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE   = "${WORKSPACE}/ci_library.db"
        IMAGE_TAG  = "library-app:${BUILD_NUMBER}"
        // Добавили путь к Docker в PATH
        PATH = "C:\\Windows\\System32;C:\\Program Files\\Docker\\Docker\\resources\\bin;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${env.PATH}"
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
                bat 'python --version || python3 --version'
            }
        }

        stage('Install') {
            steps {
                bat '''
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                    if not exist reports mkdir reports
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
            steps {
                bat "docker build -t %IMAGE_TAG% -t library-app:latest ."
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    docker compose down
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