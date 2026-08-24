# 06 Training Usage

이 문서는 합성 mp4를 학습 데이터로 사용할 때의 준비 방법을 설명한다.

## 기본 사용 방식

이 폴더의 `augmented.mp4`는 원본 episode 전체를 대체하는 파일이 아니다.

원본 episode 안의 top 영상만 교체해서 사용한다.

원본에서 교체할 파일:

```text
videos/observation.images.top/chunk-000/file-000.mp4
```

합성 결과에서 가져올 파일:

```text
{date}/erase_{target_shape}/{inserted_shape}/{episode_name}/augmented.mp4
```

나머지 데이터는 원본 episode의 것을 그대로 사용한다.

- action
- state
- parquet
- meta
- wrist 영상
- 기타 원본 파일

## 추천 준비 순서

1. `placement_manifest.csv`를 열어 전체 분포를 확인한다.
2. `target_shape`, `inserted_shape`, `target_side`, `placement_side`를 확인한다.
3. 관심 있는 row의 `output_video`를 재생한다.
4. 같은 row의 `debug_dir/placement_preview.png`를 확인한다.
5. 더 자세히 확인하려면 `metadata_json`을 연다.
6. 배치 안전성이 궁금하면 `safe_mask.png`, `unsafe_mask.png`, `motion_mask.png`, `existing_drawing_mask.png`를 확인한다.

## 경로 사용 주의

`original_input_video`는 데이터를 만들 당시의 원본 절대경로이다.

다른 PC에서는 그 경로가 없을 수 있으므로, 분석과 학습 준비에는 상대경로 컬럼을 쓰는 것이 좋다.

- `output_video`
- `asset`
- `metadata_json`
- `debug_dir`

## LeRobot dataset 변환

기존 LeRobot dataset 구조를 유지하고 top 영상만 교체하는 방식이면, 별도의 action/state 재생성 없이 사용할 수 있다.

즉, 각 원본 episode의 아래 파일만 합성본으로 교체한다.

```text
videos/observation.images.top/chunk-000/file-000.mp4
```

교체 후에는 기존 학습 파이프라인에서 episode를 다시 읽어 LeRobot dataset으로 사용하면 된다.

