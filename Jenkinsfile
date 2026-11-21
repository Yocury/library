
pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE = "${WORKSPACE}\\ci_library.db"
        DEPLOY_DIR = 'C:\\LibraryApp'
        PATH = "C:\\Windows\\System32;C:\\Windows\\System32;C:\\Windows\\System32\\WindowsPowerShell\\v1.0;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${env.PATH};C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\Vladimir\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;${env.PATH}"
    }

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        // 1. Получение исходного кода
        stage('Checkout') {
            steps {
                checkout scm
                bat 'python --version'
                echo "Ветка: ${env.BRANCH_NAME}"
            }
        }

        // 2. Установка зависимостей
        stage('Install deps') {
            steps {
                bat '''
                    python -m pip install --upgrade pip --default-timeout=60
                    python -m pip install -r requirements.txt
                '''
            }
        }

        // 3. Модульные и функциональные тесты
        stage('Test') {
            steps {
                bat '''
                    if not exist reports mkdir reports
                    python -m pytest -q --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit testResults: 'reports/junit.xml',
                          allowEmptyResults: true
                }
            }
        }

        // 4. Smoke test для main и develop
        stage('Smoke test') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                bat '''
                    python -c "import app; app.init_db()"

                    if not exist reports mkdir reports

                    start "" /B python -m flask --app app run --host 127.0.0.1 --port 5001 > reports\\app.log 2>&1

                    python -c "import socket,time,sys; s=socket.socket(); s.settimeout(1); ok=False; exec('for i in range(30):\\n try:\\n  s.connect((\\'127.0.0.1\\',5001)); ok=True; break\\n except OSError: time.sleep(1)'); sys.exit(0 if ok else 1)"

                    if errorlevel 1 (
                        echo [SMOKE] Application did not start
                        type reports\\app.log
                        exit /b 1
                    )

                    python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:5001/', timeout=5); sys.exit(0 if r.status==200 else 1)"

                    if errorlevel 1 (
                        echo [SMOKE] HTTP check failed
                        type reports\\app.log
                        exit /b 1
                    )

                    echo [SMOKE] OK
                '''
            }
            post {
                always {
                    bat '''
                        "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -Command "Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

                        exit /b 0
                    '''
                }
            }
        }

        // 5. Операции только для ветки test
        stage('Test branch operations') {
            when {
                branch 'test'
            }
            steps {
                echo 'Ветка test: выполнены автоматические тесты.'
                echo 'Развёртывание приложения не производится.'
            }
        }

        // 6. Деплой только из main
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                bat '''
                    echo [DEPLOY] Starting deployment...

                    REM Остановка старого экземпляра приложения
                    schtasks /End /TN LibraryApp >nul 2>&1

                    REM Копирование новой версии приложения
                    if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"

                    robocopy "%WORKSPACE%" "%DEPLOY_DIR%" /E /XD .git .venv venv reports __pycache__ /XF *.db

                    if errorlevel 8 (
                        echo [DEPLOY] File copy failed
                        exit /b 1
                    )

                    REM Проверка существования задачи
                    schtasks /Query /TN LibraryApp >nul 2>&1

                    if errorlevel 1 (
                        echo [DEPLOY] Scheduled task LibraryApp not found
                        exit /b 1
                    )

                    REM Запуск обновлённого приложения
                    schtasks /Run /TN LibraryApp

                    if errorlevel 1 (
                        echo [DEPLOY] Failed to start application
                        exit /b 1
                    )

                    REM Проверка доступности приложения
                    powershell -NoProfile -Command "$ok=$false; for($i=0; $i -lt 30; $i++){try{$r=Invoke-WebRequest 'http://127.0.0.1:5000/' -TimeoutSec 3; if($r.StatusCode -eq 200){$ok=$true; break}}catch{}; Start-Sleep -Seconds 1}; if(-not $ok){exit 1}"

                    if errorlevel 1 (
                        echo [DEPLOY] Application failed to start
                        schtasks /Query /TN LibraryApp /V /FO LIST
                        exit /b 1
                    )

                    echo [DEPLOY] Application successfully updated and running!
                '''
            }
        }
    }

    post {
        success {
            echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) успешно завершена."
        }

        failure {
            echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) завершилась ошибкой."
        }
    }
}
