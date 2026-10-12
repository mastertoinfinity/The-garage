
pipeline {
    agent any

    environment {
        DOCKER_IMAGE_NAME  = 'sujancr09/the-garage'
        DOCKER_TAG         = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS = 'dockerhub-credentials'

        DJANGO_SECRET_KEY    = credentials('django-secret-key')
        DJANGO_ALLOWED_HOSTS = '*'
        PYTHONUNBUFFERED     = '1'

        CONTAINER_NAME = 'garage-app'
        HOST_PORT      = '80'
        CONTAINER_PORT = '8000'
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
                echo 'Checking out Garage source code...'
                checkout scm
            }
        }

        stage('Code Lint & Quality Check') {
            steps {
                echo 'Checking Python syntax...'

                sh '''
                    set -eu

                    find . \
                        -name "*.py" \
                        -not -path "./.venv/*" \
                        -not -path "./.ci_venv/*" \
                        -not -path "./.git/*" \
                        -print0 |
                    xargs -0 -r python3 -m py_compile

                    echo "Python syntax check passed."
                '''
            }
        }

        stage('Run Django Test Suite') {
            steps {
                echo 'Running Django tests...'

                sh '''
                    set -eu

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
                echo 'Building Garage Docker image...'

                sh '''
                    set -eu

                    docker build \
                        --tag ${DOCKER_IMAGE_NAME}:${DOCKER_TAG} \
                        --tag ${DOCKER_IMAGE_NAME}:latest \
                        .
                '''
            }
        }

        stage('Docker Image Smoke Test') {
            steps {
                echo 'Testing the Docker image...'

                sh '''
                    set -eu

                    docker rm -f garage-smoke-test 2>/dev/null || true

                    docker run -d \
                        --name garage-smoke-test \
                        -p 127.0.0.1:8009:8000 \
                        -e DJANGO_SECRET_KEY=ci-smoke-test-secret-key \
                        -e DJANGO_DEBUG=True \
                        -e DJANGO_ALLOWED_HOSTS='*' \
                        ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}

                    trap 'docker rm -f garage-smoke-test >/dev/null 2>&1 || true' EXIT

                    sleep 10

                    curl --retry 5 \
                        --retry-connrefused \
                        --retry-delay 2 \
                        --fail \
                        http://127.0.0.1:8009/

                    echo "Docker smoke test passed."
                '''
            }
        }

        stage('Push to Container Registry') {
            steps {
                echo 'Pushing image to Docker Hub...'

                withCredentials([
                    usernamePassword(
                        credentialsId: "${DOCKER_CREDENTIALS}",
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )
                ]) {
                    sh '''
                        set -eu
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

        stage('Deploy to EC2') {
            steps {
                echo 'Deploying Garage to the EC2 Docker host...'

                // Safety check: the target must be the intended EC2 host.
                // This stage assumes Jenkins runs on that same host.
                sh '''
                    set -eu

                    # Pull the exact image built by this pipeline.
                    docker pull ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}

                    # Start the replacement container.
                    # Keep the existing container until the new one starts.
                    docker rm -f garage-app-new 2>/dev/null || true

                    docker run -d \
                        --name garage-app-new \
                        --restart unless-stopped \
                        -p ${HOST_PORT}:${CONTAINER_PORT} \
                        -e DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
                        -e DJANGO_ALLOWED_HOSTS="$DJANGO_ALLOWED_HOSTS" \
                        -e PYTHONUNBUFFERED="$PYTHONUNBUFFERED" \
                        ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}

                    # Wait for the new container to become ready.
                    sleep 10

                    # Verify that the application responds before
                    # replacing the previous container.
                    if ! curl --silent --show-error --fail \
                        http://127.0.0.1:${HOST_PORT}/ >/dev/null; then
                        echo "Deployment health check failed."
                        docker logs garage-app-new
                        docker rm -f garage-app-new
                        exit 1
                    fi

                    # The new container is healthy. Replace the old one.
                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true
                    docker rename garage-app-new ${CONTAINER_NAME}

                    echo "Garage deployment completed successfully."
                    docker ps --filter name=${CONTAINER_NAME}
                '''
            }
        }
    }

    post {
        always {
            echo 'Cleaning up temporary build artifacts...'

            sh '''
                rm -rf .ci_venv
                docker rm -f garage-smoke-test 2>/dev/null || true
            '''

            cleanWs()
        }

        success {
            echo 'SUCCESS: Garage tested, published, and deployed.'
        }

        failure {
            echo 'FAILED: Check the Jenkins Console Output.'
        }
    }
}
