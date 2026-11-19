pipeline {
    agent any

    environment {
        SECRET_KEY = 'ci-secret'
        DATABASE   = "${WORKSPACE}\\ci_library.db"
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
                    python -m pip install --upgrade pip --default-timeout=60 || exit /b 0
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
                    junit testResults: 'reports/junit.xml', allowEmptyResults: true
                }
            }
        }

        stage('Smoke test') {
            steps {
                bat '''
                python -c "import app; app.init_db()"

                    if not exist reports mkdir reports

                    start "" /B python -m flask --app app run --host 127.0.0.1 --port 5000 > reports\\app.log 2>&1

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

                    python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5); sys.exit(0 if r.status==200 else 1)"
                    if errorlevel 1 (
                        echo [SMOKE] / returned non-200
                        type reports\\app.log
                        exit /b 1
                    )

                    taskkill /F /IM python.exe /T >nul 2>&1
                    echo [SMOKE] OK
                '''
            }
            post {
                always {
                    bat 'taskkill /F /IM python.exe /T >nul 2>&1 || exit /b 0'
                }
            }
        }

stage('Deploy') {
    when { branch 'main' }
    steps {
        bat '''
            REM 1. Остановить старое приложение (если задачи нет — не страшно)
            schtasks /End /TN LibraryApp >nul 2>&1

            REM 2. Убедиться, что задача вообще существует
            schtasks /Query /TN LibraryApp >nul 2>&1
            if errorlevel 1 (
                echo [DEPLOY] task LibraryApp not found. Create it once manually, see Jenkinsfile comments.
                exit /b 1
            )

            REM 3. Запустить заново
            schtasks /Run /TN LibraryApp
            if errorlevel 1 (
                echo [DEPLOY] schtasks /Run failed
                exit /b 1
            )

            REM 4. Подождать и проверить, что сайт отвечает
            timeout /t 7 /nobreak >nul
            python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5); sys.exit(0 if r.status==200 else 1)"
            if errorlevel 1 (
                echo [DEPLOY] app failed to start after deploy
                exit /b 1
            )
            echo [DEPLOY] OK
        '''
    }
}
    }

    post {
        success { echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) — приложение работает" }
        failure { echo "Сборка ${env.BUILD_NUMBER} (${env.BRANCH_NAME}) упала" }
    }
}