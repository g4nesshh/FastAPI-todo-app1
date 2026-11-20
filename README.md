# Todo app (FastAPI + React)

One container: FastAPI serves the API (`/api/todos`), health check (`/health`) and the built React app on port 8000.

## Run locally

```bash
docker build -t todo-app .
docker run --rm -p 8000:8000 todo-app
# open http://localhost:8000
```

Dev mode (hot reload):

```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload      # :8000
cd frontend && npm install && npm run dev                                       # :5173
```

## Push to ECR

```bash
export AWS_REGION=ap-south-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REPO=todo-app

aws ecr create-repository --repository-name $REPO --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build --platform linux/amd64 -t $REPO .
docker tag $REPO:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:latest
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:latest
```

## Deploy on ECS (Fargate)

1. Edit `task-definition.json`: replace `<ACCOUNT_ID>` and `<REGION>`.
2. Make sure the `ecsTaskExecutionRole` role exists (policy: `AmazonECSTaskExecutionRolePolicy`).
3. Register and run:

```bash
aws ecs create-cluster --cluster-name todo-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster todo-cluster --service-name todo-service \
  --task-definition todo-app --desired-count 1 --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<SUBNET_ID>],securityGroups=[<SG_ID>],assignPublicIp=ENABLED}"
```

4. Security group must allow inbound TCP **8000**.
5. Find the task's public IP (ECS console -> task -> Network) and open `http://<PUBLIC_IP>:8000`.

With an ALB: target group port 8000, health check path `/health`.

## Notes

- Data is stored in SQLite at `/tmp/todos.db`, so it resets when the task restarts. Fine for testing. For persistence, swap in RDS/DynamoDB.
- Apple Silicon: keep `--platform linux/amd64` when building, or Fargate will fail with an exec format error (or set the task's `runtimePlatform` to ARM64).
"# FastAPI-todo-app1" 
