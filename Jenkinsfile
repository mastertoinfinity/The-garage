
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY      = 'docker.io'
        DOCKER_IMAGE_NAME    = 'sujancr09/the-garage'
        DOCKER_TAG           = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS   = 'dockerhub-credentials'

        DJANGO_SECRET_KEY    = credentials('django-secret-key')
        DJANGO_ALLOWED_HOSTS = '*'
        PYTHONUNBUFFERED     = '1'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo "===> Checking out repository..."
                checkout scm
            }
        }

        stage('Code Lint & Quality Check') {
            steps {
                echo "===> Verifying Python syntax..."

                sh '''
                    set -e

                    python3 -m py_compile $(find . \
                        -name "*.py" \
                        -not -path "./.venv/*" \
                        -not -path "./.ci_venv/*" \
                        -not -path "./.git/*")

                    echo "Python syntax check passed."
                '''
            }
        }

        stage('Run Django Test Suite') {
            steps {
                echo "===> Executing Django tests..."

                sh '''
                    set -e

                    python3 -m venv .ci_venv
                    . .ci_venv/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt

                    python manage.py test

                    deactivate
                    echo "Django tests passed."
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "===> Building Garage Docker image..."

                sh '''
                    set -e

                    docker build \
                        --tag ${DOCKER_IMAGE_NAME}:${DOCKER_TAG} \
                        --tag ${DOCKER_IMAGE_NAME}:latest \
                        .
                '''
            }
        }

        stage('Docker Image Smoke Test') {
            steps {
                echo "===> Testing the Docker container..."

                sh '''
                    set -e

                    docker rm -f garage_smoke_test 2>/dev/null || true

                    docker run -d \
                        --name garage_smoke_test \
                        -p 8009:8000 \
                        -e DJANGO_SECRET_KEY="ci-smoke-test-secret-key" \
                        -e DJANGO_DEBUG="True" \
                        -e DJANGO_ALLOWED_HOSTS="*" \
                        ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}

                    sleep 10

                    curl --retry 5 \
                        --retry-connrefused \
                        --retry-delay 2 \
                        --fail \
                        http://127.0.0.1:8009/

                    echo "Docker smoke test passed."
                '''
            }

            post {
                always {
                    sh 'docker rm -f garage_smoke_test 2>/dev/null || true'
                }
            }
        }

        stage('Push to Container Registry') {
            steps {
                echo "===> Pushing image to Docker Hub..."

                withCredentials([
                    usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )
                ]) {
                    sh '''
                        set -e
                        set +x

                        echo "$DOCKER_PASS" | docker login \
                            --username "$DOCKER_USER" \
                            --password-stdin

                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE_NAME}:latest
                    '''
                }
            }

            post {
                always {
                    sh 'docker logout || true'
                }
            }
        }
    }

    post {
        always {
            echo "===> Cleaning up temporary build artifacts..."

            sh '''
                rm -rf .ci_venv
                docker rm -f garage_smoke_test 2>/dev/null || true
            '''

            cleanWs()
        }

        success {
            echo "Pipeline succeeded! Garage app tested and Docker image published."
        }

        failure {
            echo "Pipeline failed! Check the Console Output for details."
        }
    }
}
