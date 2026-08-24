# Whiteboard Shape Augmentation Docs

이 폴더는 화이트보드 도형 지우기 task용 합성 데이터 패키지를 설명한다.

실제 mp4 결과, metadata, debug 이미지, 사용 asset, 전체 manifest가 함께 들어 있다.

## 문서 목록

| 문서 | 내용 |
| --- | --- |
| `01_overview.md` | 전체 목적, 데이터 개수, 폴더 구조 |
| `02_assets.md` | 합성에 사용한 asset 구성과 생성 방식 |
| `03_placement_policy.md` | 목표 도형/방해 도형 배치 원칙 |
| `04_manifest_and_metadata.md` | `placement_manifest`와 `placement_metadata.json` 읽는 법 |
| `05_debug_review.md` | debug 폴더와 mask 이미지 확인 방법 |
| `06_training_usage.md` | 학습 데이터로 사용할 때의 파일 교체 방식 |



## 현재 패키지 요약

| 항목 | 개수 |
| --- | ---: |
| 합성 mp4 | 315 |
| placement metadata | 315 |
| debug 폴더 | 315 |
| placement preview 이미지 | 315 |
| asset PNG | 300 |
