# 01 Overview

이 폴더는 화이트보드 도형 지우기 task를 위한 기존 합성 데이터 패키지이다.

원본 영상에는 지워야 할 목표 도형이 하나 있다. 이 패키지는 그 영상에 목표 도형과 다른 종류의 도형을 하나 더 넣어서, 로봇이 명령에 맞는 도형만 지우도록 학습시키기 위한 데이터를 담고 있다.

예를 들어 `erase the circle` 영상이라면 원은 지워야 할 목표 도형이고, 새로 추가된 삼각형이나 사각형은 방해 도형이다.

## 핵심 파일

| 파일/폴더 | 설명 |
| --- | --- |
| `placement_manifest.csv` | 전체 315개 합성 결과를 한눈에 보는 표 |
| `placement_manifest.json` | 같은 내용을 JSON으로 저장한 파일 |
| 날짜별 폴더 | 실제 합성 mp4, metadata, debug 이미지가 들어 있는 폴더 |
| `assets/` | 합성에 사용한 투명 PNG 도형 asset |
| `source_position_feasibility_preview/` | source-position 가능성을 나중에 검토하기 위해 만든 참고 preview |

## 데이터 개수

최종 합성 영상은 총 `315개`이다.

목표 도형 기준으로 균등하게 구성되어 있다.

| 목표 도형 | 개수 |
| --- | ---: |
| circle | 105 |
| rectangle | 105 |
| triangle | 105 |
| total | 315 |

날짜별 개수:

| 날짜 | 개수 |
| --- | ---: |
| 0727 | 60 |
| 0802 | 56 |
| 0804 | 26 |
| 0805 | 29 |
| 0811 | 48 |
| 0812 | 60 |
| 0813 | 36 |
| total | 315 |

## 폴더 구조

```text
lecay_code/
  0727/
  0802/
  0804/
  0805/
  0811/
  0812/
  0813/
  assets/
  source_position_feasibility_preview/
  augmentation_plan.csv
  augmentation_plan.json
  placement_manifest.csv
  placement_manifest.json
  used_assets.json
  README_FOR_ANALYSIS.md
  docs/
```

각 합성 결과는 아래 형태로 저장되어 있다.

```text
{date}/
  erase_{target_shape}/
    {inserted_shape}/
      {episode_name}/
        augmented.mp4
        placement_metadata.json
        debug/
```

예시:

```text
0727/
  erase_circle/
    rectangle/
      erase_the_circle_0726-162803/
        augmented.mp4
        placement_metadata.json
        debug/
```

