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
        disableConcurrentBuilds()
    }

    stages {
        // Эта стадия выполняется для ВСЕХ трех веток
        stage('Checkout') {
            steps {
                checkout scm
                bat 'python --version || python3 --version'
            }
        }

        // Эта стадия выполняется для ВСЕХ трех веток
        stage('Install') {
            steps {
                bat '''
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                '''
            }
        }

        // Эта стадия выполняется для ВСЕХ трех веток
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

        // Сборка образа: только для dev и main (в feature не нужно тратить время)
        stage('Build Docker Image') {
            when { anyOf { branch 'dev'; branch 'main' } }
            steps {
                bat "docker build -t %IMAGE_TAG% -t %DOCKERHUB_REPO%:latest -t %DOCKERHUB_REPO%:%BUILD_NUMBER% ."
            }
        }

        // Пуш в Docker Hub: только для main
        stage('Push to Docker Hub') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    bat 'echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin'
                    bat "docker push %DOCKERHUB_REPO%:%BUILD_NUMBER%"
                    bat "docker push %DOCKERHUB_REPO%:latest"
                }
            }
        }

        // Деплой (перезапуск контейнеров): только для main
        stage('Deploy') {
            when { branch 'main' }
            steps {
                bat '''
                    docker compose up -d --build
                '''
            }
        }
    }

    post {
        success { echo "Сборка ${env.BUILD_NUMBER} успешно завершена" }
        failure { echo "Сборка ${env.BUILD_NUMBER} упала" }
        always  { cleanWs() }
    }
}