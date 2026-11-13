pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE   = "${WORKSPACE}/ci_library.db"
        IMAGE_TAG  = "library-app:${BUILD_NUMBER}"
        DOCKERHUB_REPO = "yocurykr/library-app"
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

        }

        stage('Build Docker Image') {
            steps {
                // Тегируем образ и для локального использования, и для Docker Hub
                bat "docker build -t %IMAGE_TAG% -t %DOCKERHUB_REPO%:latest -t %DOCKERHUB_REPO%:%BUILD_NUMBER% ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                // Используем withCredentials, чтобы пароль не светился в логах
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    bat 'echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin'
                    bat "docker push %DOCKERHUB_REPO%:%BUILD_NUMBER%"
                    bat "docker push %DOCKERHUB_REPO%:latest"
                }
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    docker compose down || true
                    docker rm -f library_app || true
                    docker rm -f library_nginx || true
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