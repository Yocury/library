pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE   = "${WORKSPACE}\\ci_library.db"
        APP_HOST   = '127.0.0.1'
        APP_PORT   = '5000'
        APP_URL    = "http://127.0.0.1:5000"
        PATH = "C:\\Windows\\System32;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${env.PATH}"
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'python --version'
            }
        }

        stage('Install deps') {
            steps {
                bat '''
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            when {
                anyOf { branch 'dev'; branch 'main'; branch 'feature/library-entities' }
            }
            steps {
                // если flake8 не нужен — удалите стадию
                bat 'python -m flake8 . || exit /b 0'
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

        // === ГЛАВНАЯ ГАРАНТИЯ: приложение реально стартует и отвечает ===
        stage('Smoke test (app runs)') {
            steps {
                script {
                    bat '''
                        if not exist reports mkdir reports

                        REM 1. Запускаем приложение в фоне
                        start "" /B python -m flask --app app run --host 127.0.0.1 --port 5000 > reports\\app.log 2>&1

                        REM 2. Ждём до 30 секунд, пока порт откроется
                        set READY=0
                        for /L %%i in (1,1,30) do (
                            python -c "import socket,sys; s=socket.socket(); s.settimeout(1); sys.exit(0 if s.connect_ex(('127.0.0.1',5000))==0 else 1)" && (
                                set READY=1
                                goto :ready
                            )
                            timeout /t 1 /nobreak >nul
                        )
                        :ready

                        if "%READY%"=="0" (
                            echo [SMOKE] app did not start in 30s
                            type reports\\app.log
                            exit /b 1
                        )

                        REM 3. Дёргаем health endpoint
                        python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5); sys.exit(0 if r.status==200 else 1)"
                        if errorlevel 1 (
                            echo [SMOKE] /health returned non-200
                            type reports\\app.log
                            exit /b 1
                        )

                        REM 4. Гасим приложение
                        taskkill /F /IM python.exe /T >nul 2>&1
                        echo [SMOKE] OK
                    '''
                }
            }
            post {
                always {
                    // на всякий случай гасим всё, что могло остаться
                    bat 'taskkill /F /IM python.exe /T >nul 2>&1 || exit /b 0'
                    archiveArtifacts artifacts: 'reports/app.log', allowEmptyArchive: true
                }
            }
        }

        // === Публикация артефакта — только dev и main ===
        stage('Publish artifact') {
            when { anyOf { branch 'dev'; branch 'main' } }
            steps {
                bat '''
                    if not exist dist mkdir dist
                    python -m zipfile -c dist\\app-%BUILD_NUMBER%.zip app.py requirements.txt
                '''
                archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
            }
        }

        // === «Деплой» — только main ===
        // Раз Docker нет — перезапускаем приложение нативно.
        // Замените команды на свои (NSSM, systemd, supervisor и т.п.)
        stage('Deploy (restart app)') {
            when { branch 'main' }
            steps {
                bat '''
                    REM 1. Останавливаем старый процесс (если есть)
                    taskkill /F /IM python.exe /T >nul 2>&1 || exit /b 0

                    REM 2. Запускаем новую версию в фоне
                    start "" /B python -m flask --app app run --host 0.0.0.0 --port 5000 > deploy.log 2>&1

                    REM 3. Ждём и проверяем, что поднялось
                    timeout /t 5 /nobreak >nul
                    python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=5); sys.exit(0 if r.status==200 else 1)"
                    if errorlevel 1 (
                        echo [DEPLOY] app failed to start after deploy
                        type deploy.log
                        exit /b 1
                    )
                    echo [DEPLOY] OK
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'deploy.log', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        success { echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) успешно завершена — приложение работает" }
        failure { echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) упала — приложение НЕ задеплоено" }
    }
}