# 03 Placement Policy

이 문서는 합성 데이터에서 방해 도형을 어떤 원칙으로 배치했는지 설명한다.

## 기본 원칙

- 목표 도형과 같은 종류의 도형은 방해 도형으로 넣지 않는다.
- 방해 도형은 목표 도형과 같은 쪽에 두지 않는다.
- 방해 도형은 전체 프레임 동안 같은 위치에 고정한다.
- 방해 도형은 safe 영역 안에만 배치한다.

목표 도형별 가능한 방해 도형:

| 목표 도형 | 넣을 수 있는 방해 도형 |
| --- | --- |
| circle | triangle, rectangle |
| rectangle | circle, triangle |
| triangle | circle, rectangle |

## top/bottom 배치 기준

현재 영상은 화이트보드가 90도 돌아간 상태라서, 실제 보드 기준 좌우를 영상 좌표 기준 `top/bottom`으로 나누어 처리했다.

| 목표 도형 위치 | 방해 도형 위치 |
| --- | --- |
| top | bottom |
| bottom | top |

실제 분포:

| 목표 도형 위치 | 방해 도형 위치 | 개수 |
| --- | --- | ---: |
| bottom | top | 159 |
| top | bottom | 156 |
| total |  | 315 |

## safe 영역

방해 도형이 들어가면 안 되는 영역은 피했다.

피한 영역:

- 목표 도형 주변
- 기존 그림 또는 선이 있는 영역
- 로봇팔 움직임 영역
- 카메라선, 케이블 등 영상 내 방해 구조물
- 화이트보드 바깥
- 화이트보드 테두리 주변
- 학습 crop에서 잘릴 수 있는 영역

이 조건을 만족하는 후보 위치 중 하나를 선택해, 같은 위치에 전체 프레임 동안 방해 도형을 고정 삽입했다.

## 방해 도형 분포

삽입된 방해 도형 분포:

| 방해 도형 | 개수 |
| --- | ---: |
| circle | 111 |
| rectangle | 102 |
| triangle | 102 |
| total | 315 |

목표 도형과 방해 도형 조합:

| 목표 도형 | 방해 도형 | 개수 |
| --- | --- | ---: |
| circle | rectangle | 53 |
| circle | triangle | 52 |
| rectangle | circle | 55 |
| rectangle | triangle | 50 |
| triangle | circle | 56 |
| triangle | rectangle | 49 |
| total |  | 315 |

목표 도형 분포는 105개씩 균등하게 유지했다. 방해 도형 분포는 safe 배치 조건과 asset 선택 과정 때문에 약간 차이가 있다.
