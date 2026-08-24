# Legacy Board Y-Aware Augmentation Docs

이 폴더는 `legacy_code/`에 들어 있는 기존 합성 데이터 패키지를 설명한다.

`legacy_code/`는 source-position 재검토 이전에 만들어진 board-y-aware 합성 결과를 보관한 폴더이다. 실제 mp4 결과, metadata, debug 이미지, 사용 asset, 전체 manifest가 함께 들어 있다.

## 문서 목록

| 문서 | 내용 |
| --- | --- |
| `01_overview.md` | 전체 목적, 데이터 개수, 폴더 구조 |
| `02_assets.md` | 합성에 사용한 asset 구성과 생성 방식 |
| `03_placement_policy.md` | 목표 도형/방해 도형 배치 원칙 |
| `04_manifest_and_metadata.md` | `placement_manifest`와 `placement_metadata.json` 읽는 법 |
| `05_debug_review.md` | debug 폴더와 mask 이미지 확인 방법 |
| `06_training_usage.md` | 학습 데이터로 사용할 때의 파일 교체 방식 |

## 가장 먼저 볼 파일

```text
placement_manifest.csv
README_FOR_ANALYSIS.md
docs/01_overview.md
code/
```

## 현재 패키지 요약

| 항목 | 개수 |
| --- | ---: |
| 합성 mp4 | 315 |
| placement metadata | 315 |
| debug 폴더 | 315 |
| placement preview 이미지 | 315 |
| asset PNG | 302 |

## 코드 위치

기존 방식에 사용했던 Python 코드는 루트에 흩어두지 않고 `code/` 아래에 모았다.

```text
legacy_code/
  code/
    augment_whiteboard.py
    batch_augment_dates.py
    analyze_target_positions.py
    crop_circle_frames.py
    crop_rectangle_frames.py
    crop_triangle_frames.py
    extract_first_frames.py
    extract_shape_assets.py
    ...
    src/
      compositing.py
      placement.py
      motion.py
      roi.py
      ...
```

역할:

- `code/*.py`: 실행 스크립트
- `code/src/*.py`: 실행 스크립트에서 import하는 보조 모듈

주의: 이 코드는 당시 작업 흐름을 보존하기 위해 가져온 것이다. 재실행하려면 입력/출력 경로를 현재 환경에 맞게 확인해야 한다.
