# 04 Manifest And Metadata

이 문서는 전체 목차 파일과 episode별 metadata를 읽는 방법을 설명한다.

## placement_manifest.csv

`placement_manifest.csv`는 전체 315개 합성 결과의 목차이다.

사람이 확인할 때는 아래 컬럼을 먼저 보면 된다.

| 컬럼 | 의미 |
| --- | --- |
| `date` | 원본 날짜 |
| `episode` | 원본 episode 이름 |
| `task` | 원본 task label |
| `target_shape` | 지워야 하는 목표 도형 |
| `inserted_shape` | 추가된 방해 도형 |
| `target_side` | 목표 도형 위치 |
| `placement_side` | 방해 도형 위치 |
| `target_center_x`, `target_center_y` | 목표 도형 중심 좌표 |
| `insert_x`, `insert_y` | 방해 도형 삽입 좌표 |
| `asset` | 사용한 도형 asset |
| `output_video` | 합성 mp4 경로 |
| `metadata_json` | 상세 배치 정보 JSON |
| `debug_dir` | debug 이미지 폴더 |
| `valid_placements` | 배치 가능한 후보 위치 수 |
| `final_safe_area` | 최종 safe mask 면적 |

경로는 이 폴더 기준 상대경로이다.

따라서 폴더를 다른 PC로 옮겨도 아래 컬럼은 그대로 사용할 수 있다.

- `output_video`
- `asset`
- `metadata_json`
- `debug_dir`

## placement_manifest.json

`placement_manifest.csv`와 같은 내용을 JSON으로 저장한 파일이다.

스크립트에서 구조적으로 읽거나, 외부 분석 도구에 넘길 때 사용한다.

## placement_metadata.json

각 episode 폴더 안의 `placement_metadata.json`은 그 영상 하나에 대한 상세 기록이다.

특정 영상이 이상해 보일 때 이 파일을 보면 된다.

주로 확인할 내용:

- 어떤 방해 도형을 넣었는지
- 어떤 asset을 썼는지
- 방해 도형을 어느 좌표에 넣었는지
- 목표 도형이 어느 쪽에 있었는지
- 방해 도형을 어느 쪽에 넣었는지
- 크기, 회전, 밝기 보정이 어떻게 들어갔는지
- 배치 가능한 후보 위치가 충분했는지

중요 필드:

| 필드 | 의미 |
| --- | --- |
| `task` | 원본 task label |
| `inserted_shape` | 추가된 방해 도형 |
| `asset` | 사용한 PNG asset |
| `position.x`, `position.y` | 방해 도형 삽입 좌표 |
| `target_position.side` | 목표 도형 위치 |
| `target_position.center_x`, `target_position.center_y` | 목표 도형 중심 좌표 |
| `placement_constraints.placement_side` | 방해 도형 배치 위치 |
| `scale` | 방해 도형 크기 |
| `rotation_deg` | 방해 도형 회전 |
| `brightness` | 밝기 보정 |
| `seed` | 재현용 seed |

## augmentation_plan 주의

`augmentation_plan.csv`와 `augmentation_plan.json`은 마지막 재실행 흐름 때문에 전체 315개 계획이 아닐 수 있다.

전체 데이터를 분석할 때는 아래 두 파일을 기준으로 사용한다.

```text
placement_manifest.csv
placement_manifest.json
```

