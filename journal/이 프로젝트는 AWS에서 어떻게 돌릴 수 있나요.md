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

## PREPARING YOUR ENVIRONMENT

#### **도커 이미지를 빌드하려다가 아래와 같은 에러가 날 수 있습니다.**
PS C:\Users\chaed\Downloads\bedrock-reliability-lab-main\bedrock-reliability-lab-main> docker build --platform linux/amd64  -t bedrock-reliability-lab:v0.1 .
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
PS C:\Users\chaed\Downloads\bedrock-reliability-lab-main\bedrock-reliability-lab-main>

**Docker 명령어는 실행됐지만, Docker Desktop의 Linux 엔진에 연결하지 못한 상태일 경우입니다.** 보통 Docker Desktop이 꺼져 있거나 엔진이 아직 시작되지 않았을 때 발생합니다. 프로젝트 빌드는 아직 시작되지 않았어요.

다음 순서로 진행하세요.

**1. Docker Desktop을 실행하세요**

Windows 시작 메뉴에서 **Docker Desktop**을 열고, 엔진이 실행 중이라는 표시가 나올 때까지 기다리세요. Windows에서도 Docker Desktop의 Linux 엔진으로 이 프로젝트를 빌드할 수 있습니다. [Docker Docs](https://docs.docker.com/desktop/features/wsl/?utm_source=chatgpt.com)

**2. 같은 PowerShell에서 연결을 확인하세요**

```powershell
docker info
```

오류 없이 `Server` 정보가 나오고 `OSType: linux`가 표시되면 준비된 것입니다.

**3. 빌드 명령을 다시 실행하세요**

```powershell
docker build --platform linux/amd64 -t bedrock-reliability-lab:v0.1 .
```

**Docker Desktop을 켰는데도 같은 오류가 나면**, 다음을 확인하세요.

- Docker Desktop의 **Settings → General → Use WSL 2 based engine**을 활성화하고 적용합니다.
- 작업표시줄 Docker 아이콘 메뉴에 **Switch to Linux containers**가 보이면 선택하세요. **Switch to Windows containers**가 보인다면 이미 Linux 모드입니다. [Docker Docs](https://docs.docker.com/desktop/features/wsl/?utm_source=chatgpt.com)
- Docker Desktop을 종료한 뒤 다시 실행하고 `docker info`를 재시도합니다.

그래도 엔진이 시작되지 않으면 아래 명령으로 WSL 상태를 확인하세요.

```powershell
wsl --status
wsl --version
```

지금은 **Docker Desktop 실행 → `docker info` 확인 → 빌드 재시도**까지만 진행하면 됩니다.

**현재 `/ready`는 Bedrock 연결이나 권한을 검사하지 않습니다.** `/ask` 응답과 CloudWatch의 `bedrock_success` 로그까지 확인해야 첫 배포가 성공한 것입니다.

오늘은 **컨테이너 실행 → 질문에 대한 응답 → CloudWatch 로그 확인**까지를 목표로 잡으면 좋겠습니다. 실습을 마치면 Task를 중지하세요. 실행 자원과 모델 호출에는 비용이 발생하며, ECR 이미지와 로그는 중지 후에도 남습니다.



#### **Docker Desktop - WSL not installed
Windows Subsystem for Linux (WSL) is not installed. Install it by running wsl --install in an administrative PowerShell, then restart your computer. For more information, visit the Microsoft documentation.
wsl is not installed**

네, **WSL을 설치하면 다음 단계로 진행할 수 있습니다.** WSL은 Windows에서 Linux 환경을 실행하는 기능이며, 현재 Docker Desktop이 이를 사용하도록 설정되어 있어요.

**1. 관리자 PowerShell을 여세요**

시작 메뉴에서 `PowerShell` 검색 → 우클릭 → **관리자 권한으로 실행**한 뒤 입력하세요.

```powershell
wsl --install
```

기본적으로 WSL 2와 Ubuntu가 설치됩니다. 설치가 끝나면 작업을 저장하고 **컴퓨터를 재부팅하세요.** [Microsoft Learn](https://learn.microsoft.com/en-us/windows/wsl/install?utm_source=chatgpt.com)

**2. 재부팅 후 Docker Desktop을 실행하세요**

Ubuntu가 사용자 이름과 비밀번호를 요청하면 Linux용 계정을 만드세요. 비밀번호 입력 시 화면에 글자가 표시되지 않는 것은 정상입니다.

Docker Desktop을 열고 엔진이 시작될 때까지 기다린 뒤, PowerShell에서 확인합니다.

```powershell
docker info
```

`Server` 정보와 `OSType: linux`가 나오면 준비됐습니다.

**3. 프로젝트 폴더에서 다시 빌드하세요**

일반 PowerShell에서 다음을 실행하면 됩니다.

```powershell
cd "C:\Users\chaed\Downloads\bedrock-reliability-lab-main\bedrock-reliability-lab-main"

docker build --platform linux/amd64 -t bedrock-reliability-lab:v0.1 .
```

지금은 **WSL 설치 → 재부팅 → Docker Desktop 실행 → 빌드** 순서로 진행하세요.

#### Elastic Container Registry에 이미지 푸쉬해야 합니다.

`docker tag`는 **기존 Docker 이미지에 다른 이름표를 붙이는 명령**입니다. 원래 이름은 유지되며, 새 이름도 같은 이미지를 가리킵니다. [Docker Docs](https://docs.docker.com/reference/cli/docker/image/tag/?utm_source=chatgpt.com)

기본 문법은 다음과 같습니다.

```powershell
docker tag SOURCE_IMAGE[:TAG] TARGET_IMAGE[:TAG]
```

- `SOURCE_IMAGE[:TAG]`: 기존 이미지의 이름과 태그
- `TARGET_IMAGE[:TAG]`: 새로 붙일 이름과 태그
- 태그를 생략하면 `latest`로 해석합니다. `latest`는 이름일 뿐, 자동으로 최신 버전을 찾는 기능은 아닙니다. [Docker Docs](https://docs.docker.com/reference/cli/docker/image/tag/?utm_source=chatgpt.com)

예를 들어:

```powershell
docker tag bedrock-reliability-lab:v0.1 bedrock-reliability-lab:test
```

이 명령을 실행하면 `v0.1`과 `test`가 **같은 이미지**를 가리킵니다. 이미지 내용을 수정하거나 새로 빌드하는 것은 아닙니다.

이번 ECR 업로드에서는 **ECR 저장소 주소를 포함한 이름**을 붙입니다. 아래 계정 번호는 예시이므로, 본인의 ECR Repository URI로 바꾸세요.

```powershell
docker tag bedrock-reliability-lab:v0.1 123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-reliability-lab:v0.1
```

새 이름을 나누면 다음과 같습니다.

| 부분 | 의미 |
|---|---|
| `123456789012.dkr.ecr.ap-southeast-2.amazonaws.com` | ECR 레지스트리 주소 |
| `/bedrock-reliability-lab` | 저장소 이름 |
| `:v0.1` | 이미지 태그 |

**여기까지는 내 컴퓨터에서 이름을 붙인 것뿐입니다.** ECR 로그인 후 실제 업로드는 별도의 명령으로 합니다.

```powershell
docker push 123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-reliability-lab:v0.1
```

따라서 작업 순서는 **`build`로 이미지 생성 → `tag`로 ECR용 이름 부여 → `push`로 업로드**입니다.


## ECS Fargate에 실행 설정을 만들고, 컨테이너 하나를 실행하는 단계.

# Bedrock Reliability Lab — ECS IAM 역할 설정 가이드

AWS Console에서 ECS Fargate용 IAM 역할 두 개를 만들고 Task Definition에 연결하는 방법입니다.

- 기준일: 2026-10-15
- 실습 리전: Sydney (`ap-southeast-2`)
- 전제: 같은 AWS 계정의 private ECR에 앱 이미지를 업로드한 상태
- 범위: IAM 설정. 이 문서 자체가 ECS 배포를 자동 실행하지는 않습니다.
- 콘솔의 언어와 업데이트에 따라 메뉴 이름이 조금 다를 수 있습니다.

## 1. 두 역할의 차이

| 역할 이름 | ECS에서 선택하는 항목 | 용도 |
| --- | --- | --- |
| `ecsTaskExecutionRole` | Task execution role | ECS/Fargate가 ECR 이미지 다운로드 및 CloudWatch 로그 전송 |
| `bedrock-reliability-lab-app` | Task role | 컨테이너 안의 Python 앱이 Bedrock 호출 |

**Trust policy**는 “누가 이 역할을 사용할 수 있는가”, **Permissions policy**는 “이 역할로 무엇을 할 수 있는가”를 정합니다.

두 역할 모두 ECS Task가 사용하므로 신뢰 대상은 `ecs-tasks.amazonaws.com`입니다. 권한 정책은 서로 다릅니다.

## 2. ecsTaskExecutionRole 생성

### 2.1. IAM 열기 및 기존 역할 확인

1. AWS Console 상단 검색창에 **IAM**을 입력합니다.
2. IAM을 엽니다.
3. 왼쪽 메뉴에서 **Roles**를 선택합니다.
4. 검색창에 `ecsTaskExecutionRole`을 입력합니다.
5. 이미 있으면 역할을 열고 아래 2.6의 검증을 진행합니다.
6. 없으면 **Create role**을 선택합니다.

IAM 역할은 계정 단위입니다. ECS와 CloudWatch 리전은 이후 Sydney로 맞춥니다.

### 2.2. 신뢰할 서비스 선택

**Select trusted entity** 화면에서 다음을 선택합니다.

| 항목 | 선택 |
| --- | --- |
| Trusted entity type | AWS service |
| Service or use case | Elastic Container Service |
| Use case | Elastic Container Service Task |

**Next**를 누릅니다.

EC2용 역할이 아니라 **ECS Task용 역할**을 선택해야 합니다.

### 2.3. 권한 정책 선택

**Add permissions** 화면에서:

1. 검색창에 아래 정책 이름을 입력합니다.

   `AmazonECSTaskExecutionRolePolicy`

2. 검색 결과에서 정확히 일치하는 정책의 체크박스를 선택합니다.
3. 정책 유형이 **AWS managed**인지 확인합니다.
4. **Next**를 누릅니다.

이 정책의 ARN은 다음과 같습니다.

```text
arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

이 정책으로 ECR 인증·이미지 다운로드 및 CloudWatch 로그 스트림 생성·로그 전송 권한을 부여합니다.

**로그 그룹 생성 권한 `logs:CreateLogGroup`은 이 관리형 정책에 포함되지 않습니다.**
따라서 이번 가이드에서는 로그 그룹을 콘솔에서 미리 생성합니다(4절).

### 2.4. 역할 이름과 설명 입력

**Name, review, and create** 화면에 입력합니다.

- Role name: `ecsTaskExecutionRole`
- Description: `Allows ECS to pull container images from ECR and send container logs to CloudWatch Logs.`

이름 자체가 권한을 부여하지는 않습니다. 연결한 정책이 실제 권한을 결정합니다.

### 2.5. 검토 후 생성

**Step 1: Select trusted entities**에서 아래와 같은 Trust policy인지 확인합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

`Service`가 문자열 대신 배열로 표시되거나 빈 `Sid`가 있어도 괜찮습니다.

**Step 2: Add permissions**에는 `AmazonECSTaskExecutionRolePolicy`가 보여야 합니다.

이상이 없으면 **Create role**을 누릅니다.

### 2.6. 생성 결과 확인

1. **IAM → Roles → ecsTaskExecutionRole**을 엽니다.
2. **Permissions** 탭에 `AmazonECSTaskExecutionRolePolicy`가 있는지 확인합니다.
3. **Trust relationships** 탭에서 신뢰 대상이 `ecs-tasks.amazonaws.com`인지 확인합니다.

정책이 빠졌다면 **Permissions → Add permissions → Attach policies**에서 위 관리형 정책을 찾아 연결합니다.

Trust policy가 다르면 **Trust relationships → Edit trust policy**에서 위 JSON으로 수정합니다.

이제 execution role 준비가 끝났습니다. 아직 앱을 실행한 상태는 아닙니다.

## 3. bedrock-reliability-lab-app 생성

### 3.1. 역할 생성

1. **IAM → Roles**에서 `bedrock-reliability-lab-app`이 이미 있는지 확인합니다.
2. 없다면 **Create role**을 선택합니다.
3. **AWS service → Elastic Container Service → Elastic Container Service Task**를 선택합니다.
4. **Next**를 누릅니다.
5. **Add permissions**에서는 정책을 선택하지 않고 **Next**를 누릅니다.
6. Role name에 `bedrock-reliability-lab-app`을 입력합니다.
7. Description에 `Allows the ECS application to invoke the selected Amazon Bedrock model.`을 입력합니다.
8. Trust policy의 서비스가 `ecs-tasks.amazonaws.com`인지 확인합니다.
9. **Create role**을 누릅니다.

이미 있으면 새로 만들지 않고 기존 역할을 엽니다.

### 3.2. 사용할 Bedrock 모델 확인

Bedrock 콘솔에서 Sydney 리전을 선택하고 사용할 모델 또는 inference profile의 정보를 확인합니다.

- 모델 직접 호출: 모델 ID와 foundation model ARN
- Inference profile 호출: profile ID/ARN과 연결된 모든 foundation model ARN

선택한 모델이 앱의 Converse API 및 system 메시지를 지원하는지 확인합니다. 모델 접근 조건·구독·조직 정책도 별도로 충족해야 합니다. IAM Allow만으로 모든 접근 조건이 해결되는 것은 아닙니다.

### 3.3. Inline policy 편집기 열기

1. **IAM → Roles → bedrock-reliability-lab-app**을 엽니다.
2. **Permissions** 탭을 선택합니다.
3. **Add permissions → Create inline policy**를 선택합니다.
4. 정책 편집기에서 **JSON**을 선택합니다.
5. 아래 A 또는 B 중 실제 호출 방식에 맞는 정책 하나를 입력합니다.

현재 앱의 비스트리밍 `converse()` 호출에는 `bedrock:InvokeModel` 권한이 필요합니다.

### A. Foundation model 직접 호출

아래 `REPLACE_WITH_MODEL_ID`를 실제 모델 ID로 교체합니다. Sydney에서 직접 호출 가능한 모델인 경우에 사용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeSelectedModel",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:ap-southeast-2::foundation-model/REPLACE_WITH_MODEL_ID"
    }
  ]
}
```

Foundation model ARN에는 계정 번호가 없으므로 `ap-southeast-2::foundation-model`의 콜론 두 개는 정상입니다.

앱 환경변수 `BEDROCK_MODEL_ID`에는 해당 모델 ID를 사용합니다.

### B. Inference profile 호출

아래 자리표시자를 실제 ARN으로 바꿉니다. 연결된 모든 모델 ARN을 포함하도록 배열 항목 수를 조정합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeSelectedProfileAndModels",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "REPLACE_WITH_INFERENCE_PROFILE_ARN",
        "REPLACE_WITH_FOUNDATION_MODEL_ARN_1",
        "REPLACE_WITH_FOUNDATION_MODEL_ARN_2"
      ]
    }
  ]
}
```

Profile ARN뿐 아니라 연결된 각 리전의 foundation model ARN도 허용해야 합니다.
예제의 자리표시자를 그대로 저장하지 마세요.

앱 환경변수 `BEDROCK_MODEL_ID`에는 해당 inference profile ID 또는 ARN을 사용합니다.

### 3.4. 정책 저장 및 확인

1. 실제 값으로 교체한 JSON에 오류가 없는지 확인합니다.
2. **Next**를 누릅니다.
3. Policy name에 `bedrock-reliability-lab-invoke`를 입력합니다.
4. **Create policy**를 누릅니다.
5. 역할의 **Permissions** 탭에 정책이 보이는지 확인합니다.
6. **Trust relationships**의 서비스가 `ecs-tasks.amazonaws.com`인지 확인합니다.

## 4. CloudWatch 로그 그룹 미리 생성

1. AWS Console에서 **CloudWatch**를 엽니다.
2. 리전을 **Sydney / ap-southeast-2**로 맞춥니다.
3. **Logs → Log groups → Create log group**을 선택합니다.
4. 이름에 `/ecs/bedrock-reliability-lab`을 입력합니다.
5. 실습용 보존 기간을 **7일**로 선택하고 생성합니다.

이 작업은 현재 콘솔 사용자 권한으로 수행합니다. Execution role에 로그 그룹 생성 권한을 추가할 필요가 없습니다.

## 5. ECS Task Definition에 연결

**ECS → Task definitions → Create new task definition**에서 설정합니다.
기존 Task Definition이 있으면 **Create new revision**으로 수정합니다.

| 항목 | 값 |
| --- | --- |
| Family | bedrock-reliability-lab |
| Launch type | AWS Fargate |
| Operating system / Architecture | Linux / X86_64 |
| Task CPU / Memory | 0.25 vCPU / 1 GB |
| Task role | bedrock-reliability-lab-app |
| Task execution role | ecsTaskExecutionRole |
| Container name | app |
| Image URI | 본인 ECR 이미지 URI 및 태그 |
| Container port | 8000 / TCP |
| AWS_REGION 환경변수 | ap-southeast-2 |
| BEDROCK_MODEL_ID 환경변수 | 선택한 모델 또는 profile ID/ARN |
| Log driver | awslogs |
| Log group | /ecs/bedrock-reliability-lab |
| Log region | ap-southeast-2 |
| Log stream prefix | ecs |

이미 로그 그룹을 만들었다면 자동 로그 그룹 생성 옵션(`awslogs-create-group`)은 끄거나 생략합니다.

Dockerfile의 기본 실행 명령을 그대로 사용합니다. Task role을 연결하면 Boto3가 ECS 임시 자격 증명을 사용할 수 있으므로 컨테이너에 장기 액세스 키를 넣지 않습니다.

새 revision을 저장해도 기존 실행 Task가 자동으로 바뀌지는 않습니다. 새 revision으로 Task를 실행하거나 Service를 업데이트해야 합니다.

## 6. 실행 및 검증

IAM 설정 후에는 ECS Cluster에서 Fargate Task 하나를 실행합니다.
첫 실습의 네트워크 설정은 다음과 같습니다.

- Internet Gateway 경로가 있는 public subnet
- Assign public IP 활성화
- Security Group inbound: TCP 8000, 출발지는 본인 공인 IP /32
- Outbound: ECR, CloudWatch, Bedrock HTTPS 접속을 허용

현재 앱에는 사용자 인증이 없습니다. 이 HTTP 접근은 민감한 데이터를 넣지 않는 제한된 실습용입니다.

Task가 RUNNING이면 public IP로 접속합니다.

```text
http://TASK_PUBLIC_IP:8000/docs
```

| 검증 | 성공 기준 |
| --- | --- |
| Task 실행 | RUNNING 상태, 이미지 다운로드 오류 없음 |
| GET /health | 200 응답 |
| GET /ready | 모델 ID 설정 확인; 실제 Bedrock 접근 검사는 아님 |
| POST /ask | 실제 모델 답변 반환 |
| CloudWatch Logs | 요청 로그 및 bedrock_success 확인 |

실습을 마치면 standalone Task를 중지합니다. Service로 실행했다면 desired count를 0으로 조정해야 재생성을 막을 수 있습니다.

## 7. 자주 막히는 지점

| 증상 | 확인할 내용 |
| --- | --- |
| 역할이 ECS 목록에 없음 | 역할 목록 새로고침, 계정 일치, ECS Task 신뢰 관계 |
| 역할 연결 시 AccessDenied | 콘솔 사용자의 해당 역할에 대한 iam:PassRole 권한 |
| CannotPullContainerError | 이미지 URI/태그, execution role, ECR 정책, 네트워크 |
| 로그 그룹이 없다는 오류 | Sydney에 로그 그룹 생성 여부, 로그 그룹 이름 |
| POST /ask가 502 반환 | 앱이 Bedrock 오류를 502로 감쌈; CloudWatch의 원래 예외 확인 |
| Bedrock AccessDenied | Task role, 모델/profile ARN, SCP·permissions boundary·모델 접근 조건 |
| /ready 성공 후 /ask 실패 | /ready는 환경변수만 확인하므로 IAM 및 모델 호출은 별도 검증 필요 |

## 8. GitHub에 추가

권장 파일 경로:

```text
docs/aws-iam-roles.md
```

저장소 README.md에 다음 링크를 추가합니다.

```markdown
## AWS 배포 준비

- [ECS IAM 역할 설정 가이드](docs/aws-iam-roles.md)
```

이 문서는 콘솔 수동 설정 가이드입니다. 기존 Terraform으로 같은 이름의 역할을 이미 관리하고 있다면 중복 생성하지 말고 기존 리소스를 사용하세요. 콘솔에서 만든 역할을 이후 Terraform으로 관리할 때는 import 및 설정 일치 작업이 필요합니다.

## 공식 참고 문서

- [ECS Task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
- [AmazonECSTaskExecutionRolePolicy](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonECSTaskExecutionRolePolicy.html)
- [ECS Task IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)
- [Inference profile 권한 사전 조건](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html)
- [Fargate Task Definition 설정](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html)
- [ECS outbound networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/networking-outbound.html)

