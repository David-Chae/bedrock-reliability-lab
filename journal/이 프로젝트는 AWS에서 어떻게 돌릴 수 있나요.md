# 이 프로젝트는 AWS에서 어떻게 돌릴 수 있나요?

**지금 프로젝트는 Docker 컨테이너로 만들어서 AWS ECS Fargate에서 실행할 수 있습니다.** Fargate는 컨테이너가 돌아갈 서버를 AWS가 관리해주는 방식이에요.

파일을 확인해보니 `Dockerfile`은 준비되어 있습니다. 다만 **현재 Terraform은 IAM 역할과 Bedrock 호출 권한만 생성하며, 앱을 실행할 ECS 인프라는 아직 없습니다.**

첫 배포는 다음 순서로 진행하면 됩니다.

**1. Bedrock에서 사용할 모델을 확인합니다**

AWS 콘솔에서 리전을 **Sydney `ap-southeast-2`**로 선택하고, Bedrock Playground에서 텍스트 모델을 호출해보세요.

이 앱은 `Converse` API로 시스템 메시지를 보내므로, 해당 기능을 지원하는 모델을 선택해야 합니다. 모델 ID 또는 inference profile ID/ARN을 기록합니다. 모델별 접근 조건도 확인하세요. [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html?utm_source=chatgpt.com)

**2. Docker 이미지를 ECR에 올립니다**

ECR은 Docker 이미지를 보관하는 AWS 서비스입니다.

프로젝트의 `Dockerfile`이 있는 폴더에서 다음처럼 빌드합니다.

```bash
docker build --platform linux/amd64 \
  -t bedrock-reliability-lab:v0.1 .
```

AWS 콘솔에서 ECR private repository를 `bedrock-reliability-lab`이라는 이름으로 생성하세요. 저장소의 **View push commands**에 나오는 로그인·태그·푸시 명령을 실행하면 됩니다.

**3. ECS에 실행 설정을 만듭니다**

ECS에서 Fargate용 **Task Definition**을 생성합니다. Task Definition은 “어떤 컨테이너를 어떤 자원과 설정으로 실행할 것인가”를 정의합니다.

| 설정 | 첫 실습 값 |
|---|---|
| 운영체제·CPU 아키텍처 | Linux / X86_64 |
| CPU / 메모리 | 0.25 vCPU / 1 GB |
| Container image | ECR에 올린 이미지 URI |
| Container port | `8000` |
| `AWS_REGION` 환경변수 | `ap-southeast-2` |
| `BEDROCK_MODEL_ID` 환경변수 | 1단계에서 확인한 값 |
| 로그 | CloudWatch Logs로 전송 |

IAM 역할은 두 가지를 구분해야 합니다.

- **Task execution role:** ECS가 ECR 이미지를 가져오고 CloudWatch에 로그를 보내는 권한.
- **Task role:** 실행 중인 Python 앱이 Bedrock을 호출하는 권한. 기존 Terraform의 `bedrock-reliability-lab-app` 역할이 여기에 해당합니다.

앱에는 AWS 액세스 키를 넣지 않고 Task role을 연결합니다. [Amazon Elastic Container Service](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html?utm_source=chatgpt.com)

**주의할 설정 하나:** inference profile을 선택하면 기존 Terraform의 단일 ARN 권한으로 부족할 수 있습니다. profile ARN과 연결된 리전별 foundation model ARN을 허용하도록 수정해야 합니다. [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html?utm_source=chatgpt.com)

**4. Fargate Task 하나를 실행합니다**

첫 실습에서는 ECS cluster를 만들고 **Run task**로 하나만 실행하세요.

- Internet Gateway로 연결되는 **public subnet** 선택
- **Assign public IP** 활성화
- Security Group inbound: TCP `8000`, 출발지는 **본인의 현재 공인 IP `/32`**
- Outbound: ECR·CloudWatch·Bedrock에 접근할 수 있도록 허용

Fargate가 이 구성에서 인터넷에 접근하려면 public IP가 필요합니다. [Amazon Elastic Container Service](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/networking-outbound.html?utm_source=chatgpt.com)

현재 앱에는 사용자 인증이 없으므로, `8000` 포트를 모든 IP에 개방하지 마세요. 이 HTTP 접속은 민감한 내용을 넣지 않는 짧은 실습용입니다.

**5. 실제 호출과 로그를 확인합니다**

Task의 public IP로 접속합니다.

```text
http://<TASK_PUBLIC_IP>:8000/docs
```

FastAPI의 테스트 화면에서 다음 순서로 실행하세요.

| 요청 | 확인하는 것 |
|---|---|
| `GET /health` | 앱이 요청을 처리하는지 |
| `GET /ready` | 모델 ID 환경변수가 설정됐는지 |
| `POST /ask` | 실제 Bedrock 호출이 성공하는지 |

`/ask`에는 다음 내용을 넣으면 됩니다.

```json
{
  "question": "Explain liveness and readiness probes."
}
```

**현재 `/ready`는 Bedrock 연결이나 권한을 검사하지 않습니다.** `/ask` 응답과 CloudWatch의 `bedrock_success` 로그까지 확인해야 첫 배포가 성공한 것입니다.

오늘은 **컨테이너 실행 → 질문에 대한 응답 → CloudWatch 로그 확인**까지를 목표로 잡으면 좋겠습니다. 실습을 마치면 Task를 중지하세요. 실행 자원과 모델 호출에는 비용이 발생하며, ECR 이미지와 로그는 중지 후에도 남습니다.
