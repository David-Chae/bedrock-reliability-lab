# Bedrock Reliability Lab

A production-oriented Amazon Bedrock service built to demonstrate **GenAI + cloud reliability engineering**.

## v0.1 scope

This first milestone deliberately keeps the system small:

- FastAPI service
- Amazon Bedrock `Converse` API
- health/readiness endpoints
- request IDs and structured logs
- latency metrics in responses/logs
- least-privilege IAM policy template
- Docker support
- unit tests with Bedrock mocked
- Terraform starter infrastructure
- CI test workflow

The next milestone adds:

1. Bedrock Managed Knowledge Base (RAG)
2. S3 ingestion
3. Guardrails
4. CloudWatch dashboards/alarms
5. Terraform-managed deployment
6. failure injection + incident runbook
7. AgentCore extension

## Architecture

```text
Client
  |
  v
FastAPI service
  |
  +-- /health
  +-- /ready
  +-- /ask
        |
        v
Amazon Bedrock Runtime
        |
        v
Foundation Model

Observability:
JSON application logs
request_id
latency_ms
model_id
HTTP status

Planned:
S3 -> Bedrock Managed Knowledge Base -> Retrieve/RetrieveAndGenerate
Guardrails
AgentCore
```

## Why this project exists

The goal is not to build another chatbot demo. The goal is to be able to say:

> I built and operated a production-oriented GenAI service on AWS, secured access with IAM, added observability and health checks, tested failure modes, and extended it with managed RAG.

## Prerequisites

- Python 3.12+
- AWS CLI credentials configured
- Amazon Bedrock access in your AWS account
- Terraform 1.7+ for the infrastructure exercises

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export AWS_REGION=ap-southeast-2
export BEDROCK_MODEL_ID="<a text model/inference profile available in your account>"

uvicorn app.main:app --reload
```

Check health:

```bash
curl http://localhost:8000/health
```

Ask the model:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain the difference between liveness and readiness probes."}'
```

## Important model-access note

Do **not** hard-code a model ID copied from an old tutorial. Bedrock model availability and supported invocation methods vary by Region and model lifecycle. Choose a currently available text model or inference profile from your AWS account.

## Tests

```bash
pytest -q
```

## Docker

```bash
docker build -t bedrock-reliability-lab .
docker run --rm -p 8000:8000 \
  -e AWS_REGION=ap-southeast-2 \
  -e BEDROCK_MODEL_ID="$BEDROCK_MODEL_ID" \
  bedrock-reliability-lab
```

## Terraform starter

The first Terraform milestone creates an IAM role/policy skeleton for invoking a selected Bedrock resource.

```bash
cd infra
terraform init
terraform validate
terraform plan \
  -var='bedrock_model_resource_arn=<ARN YOU INTEND TO ALLOW>'
```

Avoid using `Resource = "*"` in the finished portfolio unless the API/resource type truly requires it.

## Milestones

### M0 — service skeleton
- [x] Bedrock runtime client
- [x] API validation
- [x] health/readiness
- [x] structured logs
- [x] tests
- [x] Docker
- [x] CI
- [x] Terraform IAM starter

### M1 — deployable AWS service
- [ ] ECR
- [ ] ECS Fargate or Lambda deployment
- [ ] API Gateway / ALB
- [ ] CloudWatch log group
- [ ] alarms
- [ ] remote Terraform state

### M2 — RAG
- [ ] S3 document bucket
- [ ] Bedrock Managed Knowledge Base
- [ ] ingestion/sync
- [ ] Retrieve/RetrieveAndGenerate path
- [ ] citation return format
- [ ] retrieval-quality test cases

### M3 — security
- [ ] Bedrock Guardrails
- [ ] prompt-injection test set
- [ ] sensitive-information tests
- [ ] KMS where appropriate
- [ ] IAM tightening
- [ ] threat model

### M4 — reliability engineering
- [ ] timeout/retry policy
- [ ] throttling handling
- [ ] load test
- [ ] latency/error SLO
- [ ] failure injection
- [ ] incident runbook
- [ ] postmortem

### M5 — agentic extension
- [ ] evaluate AgentCore architecture
- [ ] tool invocation
- [ ] policy boundaries
- [ ] agent observability

## Portfolio evidence to collect

Keep screenshots/logs for:

- successful deployment
- CloudWatch metrics
- alarm firing
- throttling/error handling
- a failed deployment and rollback
- RAG retrieval evaluation
- Guardrail intervention
- an incident write-up

Those artifacts are more valuable in an interview than a repository containing code alone.
