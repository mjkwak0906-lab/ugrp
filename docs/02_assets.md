# 02 Assets

이 문서는 `legacy_code/assets/`에 들어 있는 합성용 도형 asset을 설명한다.

## asset 역할

asset은 합성용으로 새로 그린 그림이 아니라, 실제 수집 영상에서 뽑은 도형이다.

진행 방식:

1. 단일 목표 도형 episode의 top 영상 첫 프레임을 추출했다.
2. 첫 프레임에서 목표 도형 주변을 crop했다.
3. crop된 이미지에서 도형 선 부분만 남기고 배경을 제거했다.
4. 결과를 투명 배경 PNG asset으로 저장했다.
5. 배경이 남거나 지저분한 결과는 anomaly로 분리했다.
6. anomaly 중 일부는 재처리했고, 사람이 보기에 쓸 수 있는 것만 최종 asset에 다시 포함했다.

따라서 asset은 실제 화이트보드에 그려진 선의 질감, 굵기, 흐림 정도를 어느 정도 유지한다.

## 현재 asset 구조

```text
assets/
  circle/
  rectangle/
  triangle/
  asset_index.csv
```

asset 개수:

| 도형 | asset 수 |
| --- | ---: |
| circle | 101 |
| rectangle | 101 |
| triangle | 100 |
| total | 302 |

## asset_index.csv

`asset_index.csv`는 asset의 원본 위치 정보를 보관한다.

주로 확인할 내용:

- asset 파일 경로
- 도형 종류
- 원본 episode 정보
- crop 좌표
- source center 좌표

## manifest와 연결

`placement_manifest.csv`의 `asset` 컬럼은 이 asset들을 상대경로로 가리킨다.

예:

```text
assets/rectangle/093_erase_the_rectangle_0813-184309.png
```

경로는 `legacy_code/` 기준 상대경로이므로, 폴더 전체를 다른 위치로 옮겨도 같이 따라갈 수 있다.

## 관련 코드

asset 생성과 검수에 사용한 코드는 `code/`에 들어 있다.

```text
code/
  extract_first_frames.py
  crop_circle_frames.py
  crop_rectangle_frames.py
  crop_triangle_frames.py
  extract_shape_assets.py
  build_asset_index.py
  build_records_0727_0813_assets.py
  make_line_alpha_assets.py
  mark_asset_quality_issues.py
  reprocess_quality_issue_assets.py
  organize_asset_sets.py
  review_asset_quality.py
  render_all_assets_with_regions.py
```