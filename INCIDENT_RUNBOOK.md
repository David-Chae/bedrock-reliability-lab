# Incident Runbook — v0.1

## SLO candidates

Initial targets for the lab; refine after load testing.

- Availability: 99.9% for `/ask`
- p95 application latency: establish baseline before setting target
- 5xx error rate: < 1% over a 5-minute window

Do not invent an SLO latency number before measuring the actual model.

## Failure: Bedrock AccessDeniedException

Check:

1. `BEDROCK_MODEL_ID`
2. AWS Region
3. workload IAM role
4. resource ARN allowed by IAM
5. AWS Marketplace/model prerequisites for third-party models
6. whether an inference profile is required/being used

## Failure: throttling

Check:

1. invocation rate
2. retry behavior
3. model/inference-profile limits
4. whether the client is creating a retry storm

Expected design response:

- bounded retries
- exponential backoff
- request timeout
- surface a controlled 5xx rather than hanging indefinitely

## Failure: rising latency

Check:

1. application latency
2. Bedrock invocation latency
3. token/input growth
4. retry count
5. concurrent request volume

## Failure: hallucination

This is not just an infrastructure incident.

For the RAG milestone:

1. save query + generated answer
2. inspect retrieved chunks
3. test whether retrieval failed or generation ignored evidence
4. record retrieval configuration
5. add the case to the evaluation set
