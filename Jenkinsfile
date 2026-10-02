pipeline {
    agent any

    environment {
        DOCKER_REGISTRY      = 'docker.io'
        DOCKER_IMAGE_NAME    = 'mastertoinfinity/the-garage'
        DOCKER_TAG           = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS   = 'dockerhub-credentials'
        AWS_CREDENTIALS      = 'aws-credentials'
        ANSIBLE_SSH_KEY      = 'server-ssh-key'
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
                echo "===> Verifying python code syntax and formatting..."
                sh '''
                    python3 -m py_compile $(find . -name "*.py" -not -path "./.venv/*")
                    echo "Syntax check passed successfully."
                '''
            }
        }

        stage('Run Django Test Suite') {
            steps {
                echo "===> Executing Django unit and integration tests..."
                sh '''
                    python3 -m venv .ci_venv
                    . .ci_venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python manage.py test
                    deactivate
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "===> Building Docker image ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}..."
                sh '''
                    docker build \
                        --tag ${DOCKER_IMAGE_NAME}:${DOCKER_TAG} \
                        --tag ${DOCKER_IMAGE_NAME}:latest \
                        .
                '''
            }
        }

        stage('Docker Image Smoke Test') {
            steps {
                echo "===> Testing container runtime and healthcheck..."
                sh '''
                    docker run -d --name garage_smoke_test -p 8009:8000 \
                        -e DJANGO_SECRET_KEY="ci-smoke-test-secret-key" \
                        -e DJANGO_DEBUG="True" \
                        -e DJANGO_ALLOWED_HOSTS="*" \
                        ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}
                    
                    sleep 6
                    curl -f http://127.0.0.1:8009/ || (docker logs garage_smoke_test && exit 1)
                    docker rm -f garage_smoke_test
                    echo "Docker container smoke test passed."
                '''
            }
        }

        stage('Push to Container Registry') {
            steps {
                echo "===> Pushing image to container registry..."
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}
                        docker push ${DOCKER_IMAGE_NAME}:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Terraform Infrastructure Check') {
            steps {
                dir('terraform') {
                    echo "===> Validating Terraform plan..."
                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: "${AWS_CREDENTIALS}"
                    ]]) {
                        sh '''
                            terraform init -backend=false
                            terraform validate
                        '''
                    }
                }
            }
        }

        stage('Deploy via Ansible') {
            steps {
                dir('ansible') {
                    echo "===> Executing Ansible deployment playbook..."
                    withCredentials([sshUserPrivateKey(credentialsId: "${ANSIBLE_SSH_KEY}", keyFileVariable: 'SSH_KEY_FILE', usernameVariable: 'SSH_USER')]) {
                        sh '''
                            ansible-playbook -i inventory.ini playbook.yml \
                                --private-key "$SSH_KEY_FILE" \
                                -u "$SSH_USER" \
                                --extra-vars "app_image=${DOCKER_IMAGE_NAME}:${DOCKER_TAG} django_secret_key=${DJANGO_SECRET_KEY}"
                        '''
                    }
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
            echo "Pipeline succeeded! Automotive Web App successfully tested, built, and deployed."
        }
        failure {
            echo "Pipeline failed! Please inspect logs above for details."
        }
    }
}
