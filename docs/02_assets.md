# 02 Assets

이 문서는 `assets/`에 들어 있는 합성용 도형 asset을 설명한다.

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
  anomaly/
  circle/
  rectangle/
  triangle/
  asset_index.csv
```

asset 개수:

| 도형 | asset 수 |
| --- | ---: |
| circle | 99 |
| rectangle | 101 |
| triangle | 100 |
| total | 300 |

anomaly 수량:

| shape | 개수 |
| --- | ---: |
| circle | 6 |
| rectangle | 4 |
| triangle | 5 |
| total | 15 |

anomaly 이유:

| 이유 | 개수 | 설명 |
| --- | ---: | --- |
| excluded_from_final_usable_assets | 15 | 원본 315개 후보에는 있었지만 품질 검수/수동 확인 후 최종 사용 asset 300개에는 포함하지 않음 |

## 생성 흐름

asset 생성은 크게 네 단계로 진행했다.

```text
1. 각 episode의 top 영상 첫 프레임 추출
2. 목표 도형 위치 검출 후 도형 주변 crop
3. OpenCV 기반 로컬 alpha 생성 방식으로 투명 PNG 생성
4. 품질 이상 asset을 분리/재처리/수동 제외 후 최종 asset 구성
5. 최종 asset을 source center 기준 6개 zone으로 분류
```

## crop 방식

각 도형별 crop 스크립트가 첫 프레임에서 목표 도형 후보를 찾는다.

- circle: 원형/타원형에 가까운 어두운 선 후보 탐색
- rectangle: 사각형 윤곽 후보 탐색
- triangle: 삼각형 윤곽 후보 탐색

crop 결과에는 다음 위치 정보가 기록된다.

- `source_x`
- `source_y`
- `source_width`
- `source_height`
- `source_center_x`
- `source_center_y`

이 좌표는 이후 합성 위치와 asset 원본 위치를 비교할 때 사용한다.

## OpenCV 기반 로컬 alpha 생성 방식

이 방식은 외부 웹 배경 제거가 아니라 OpenCV 기반 로컬 처리이다.

핵심 원칙:

- 원본 crop 위치는 유지
- 원본 crop 이미지의 RGB 픽셀은 최대한 그대로 유지
- 배경 제거는 alpha 채널만 새로 계산
- gray threshold로 어두운 펜 선 후보를 찾음
- 작은 잡음 component는 제거
- edge/blur/dilate는 기본적으로 강하게 쓰지 않음

이렇게 한 이유:

- edge 기반 처리는 흰 테두리나 이중선처럼 보이는 문제가 있었음
- 학습용 asset은 원본 영상과 색감/선 두께가 달라지면 합성 티가 커질 수 있음
- 따라서 선 색은 원본을 보존하고, 투명도만 새로 만드는 방식이 더 안정적이라고 판단함

## 품질 검수 및 제외

자동 생성 후 품질 문제가 있는 asset을 따로 분리했다.

주요 문제 유형:

- 배경이 일부 남은 경우
- crop이 잘린 경우
- 선 주변이 지저분한 경우
- 오른쪽 위 등 특정 배경 조각이 남은 경우

일부는 재처리를 시도했고, 그래도 부적절한 asset은 최종 사용 대상에서 제외했다.

현재 `assets/circle`, `assets/rectangle`, `assets/triangle`에는 최종 사용 대상 `300개`가 들어 있다.

사용 대상에서 제외된 `15개`는 `assets/anomaly/`에 따로 보관한다.

`assets/anomaly/missing_anomaly_manifest.csv`에는 다음 정보가 있다.

- 원본 asset 경로
- anomaly 폴더 내부 상대경로
- 제외 이유
- 원본 source 좌표
- shape/date/episode 정보


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

경로는 repository root 기준 상대경로이므로, 폴더 전체를 다른 위치로 옮겨도 같이 따라갈 수 있다.
