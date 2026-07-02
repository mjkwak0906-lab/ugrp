# UGRP Piper LeRobot 녹화 도구

Piper 마스터-슬레이브 텔레옵으로 LeRobot 데이터셋을 녹화하기 위한 팀 작업용 저장소입니다.

## 목표 작업

- 입력: 상방 카메라, 팔목 카메라, Piper follower 현재 상태, task text `write AIIII`
- 시연: leader Piper를 손으로 조종해서 follower Piper가 펜을 집고 화이트보드에 `AIIII` 쓰기
- 출력: imitation learning 학습에 사용할 LeRobot dataset

## 저장소 역할

이 저장소는 `lerobot_robot_piper` 플러그인을 직접 포함하지 않습니다. Piper 플러그인은 서버에 따로 설치하고, 이 저장소는 우리 팀의 실행 스크립트와 실험 절차만 관리합니다.

```bash
git clone https://github.com/WeGo-Robotics/lerobot_robot_piper.git
cd lerobot_robot_piper
pip install -e .
```

## 빠른 시작

설정 파일 생성:

```bash
cp configs/recording.env.example configs/recording.env
```

`configs/recording.env`에서 서버 환경에 맞게 수정:

- `LEADER_PORT`: leader arm CAN 포트
- `FOLLOWER_PORT`: follower arm CAN 포트
- `TOP_CAM`: 상방 카메라 index
- `WRIST_CAM`: 팔목 카메라 index
- `HF_USER` 또는 `DATASET_REPO_ID`: 저장할 dataset 이름

Linux 서버에서 CAN 초기화:

```bash
bash scripts/setup_can.sh
```

카메라 번호 확인:

```bash
python /path/to/lerobot_robot_piper/camera_check.py
```

텔레옵 점검:

```bash
bash scripts/teleop_smoke_test.sh
```

`write AIIII` 녹화:

```bash
bash scripts/record_write_light.sh
```

## Python 스크립트

Bash 스크립트는 내부적으로 Python 스크립트를 호출합니다. 명령만 확인하고 하드웨어를 건드리지 않으려면 `--dry-run`을 사용합니다.

```bash
python3 scripts/wego_teleop_smoke.py --dry-run
python3 scripts/wego_record_write_light.py --dry-run
```

녹화 후 dataset 구조 확인:

```bash
python3 scripts/wego_dataset_check.py --dataset-repo-id your_hf_name/piper_write_light --episode 0
```

## 파일 구성

| 파일 | 역할 |
|---|---|
| `configs/recording.env.example` | 서버별 설정 예시 |
| `scripts/setup_can.sh` | Linux CAN 포트 초기화 |
| `scripts/teleop_smoke_test.sh` | 텔레옵 점검용 Bash wrapper |
| `scripts/record_write_light.sh` | 녹화용 Bash wrapper |
| `scripts/common_env.py` | Python 스크립트 공통 env 로더 |
| `scripts/wego_teleop_smoke.py` | WeGo `piper_follower`/`piper_leader` 기반 텔레옵 점검 |
| `scripts/wego_record_write_light.py` | WeGo 기반 `write AIIII` dataset 녹화 |
| `scripts/wego_dataset_check.py` | LeRobot dataset feature/action/state 확인 |
| `docs/setup_checklist.md` | 실험 전 체크리스트 |
| `docs/data_collection_protocol.md` | 데이터 수집 프로토콜 |

## 안전 기본값

기본 `MAX_RELATIVE_TARGET`은 `5`입니다. leader와 follower 초기 자세가 잘 맞지 않으면 follower가 갑자기 움직일 수 있으므로 더 낮은 값으로 시작합니다.

```bash
MAX_RELATIVE_TARGET=2 bash scripts/teleop_smoke_test.sh
```

초기 자세가 계속 어긋나면 `piper-calibrate`로 zero-point를 먼저 맞춥니다.
