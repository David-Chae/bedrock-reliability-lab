### 1. Docker 명령어는 실행됐지만, Docker Desktop의 Linux 엔진에 연결하지 못한 상태

PS C:\Users\chaed\Downloads\bedrock-reliability-lab-main\bedrock-reliability-lab-main> docker build --platform linux/amd64  -t bedrock-reliability-lab:v0.1 .
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
PS C:\Users\chaed\Downloads\bedrock-reliability-lab-main\bedrock-reliability-lab-main>

**Docker 명령어는 실행됐지만, Docker Desktop의 Linux 엔진에 연결하지 못한 상태입니다.** 보통 Docker Desktop이 꺼져 있거나 엔진이 아직 시작되지 않았을 때 발생합니다. 프로젝트 빌드는 아직 시작되지 않았어요.

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


### Docker Desktop - WSL not installed

Docker Desktop - WSL not installed
Windows Subsystem for Linux (WSL) is not installed. Install it by running wsl --install in an administrative PowerShell, then restart your computer. For more information, visit the Microsoft documentation.
wsl is not installed

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


### docker tag command 용법 설명해줄래요?

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


### ECR에 이미지 저장하는데 얼마나 들어요? 한달에?

**ECR에 이미지 하나를 저장하는 비용은 보통 월 몇 센트 수준입니다.** 저장료를 **1GB당 월 US$0.10**으로 잡으면 다음과 같습니다. AWS 공식 비용 예제도 이 단가를 사용합니다. [docs.aws.amazon.com](https://docs.aws.amazon.com/solutions/latest/migration-assistant-for-amazon-opensearch-service/cost.html?utm_source=chatgpt.com)

| 총 저장 용량 | 월 저장료 |
|---|---:|
| 100MB | 약 US$0.01 |
| 300MB | 약 US$0.03 |
| 500MB | 약 US$0.05 |
| 1GB | US$0.10 |
| 10GB | US$1.00 |

예를 들어 **이번 이미지가 ECR에서 300MB라면 한 달 저장료는 약 US$0.03**입니다. 실제 크기는 ECR 저장소의 **Images → Image size**에서 확인하세요.

위 금액은 **저장료만 계산한 세금·무료 혜택 적용 전 추정치**입니다. 현재 가격 페이지를 불러오지 못해 Sydney 단가를 직접 재확인하지는 못했습니다.

**ECR에 보관하는 비용과 앱을 실행하는 비용은 별개예요.** Fargate 실행, Bedrock 호출, 로그 등에 드는 비용은 위 표에 포함되지 않습니다.
