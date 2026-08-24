# 05 Debug Review

이 문서는 episode별 `debug/` 폴더를 확인하는 방법을 설명한다.

## debug 폴더 위치

각 episode 결과 폴더에는 `debug/`가 있다.

```text
{date}/
  erase_{target_shape}/
    {inserted_shape}/
      {episode_name}/
        debug/
```

현재 패키지에는 `debug/` 폴더가 315개 있고, 각 episode마다 `placement_preview.png`가 있다.

## 가장 먼저 볼 파일

```text
debug/placement_preview.png
```

이 이미지는 첫 프레임 위에 방해 도형을 실제 배치 위치에 올려서 보여준다. 합성이 눈으로 자연스러운지 가장 빠르게 확인할 수 있다.

## 주요 debug 파일

| 파일 | 설명 |
| --- | --- |
| `first_frame.png` | 원본 top 영상 첫 프레임 |
| `placement_preview.png` | 방해 도형 배치 결과 미리보기 |
| `board_mask.png` | 화이트보드 영역 |
| `board_border_mask.png` | 보드 테두리 회피 영역 |
| `motion_mask.png` | 로봇팔 움직임 회피 영역 |
| `existing_drawing_mask.png` | 기존 도형/선 그림 회피 영역 |
| `manual_exclusion_mask.png` | 수동 제외 영역 |
| `placement_constraint_mask.png` | 위/아래 배치 제한 영역 |
| `safe_mask.png` | 최종 배치 가능 영역 |
| `unsafe_mask.png` | 배치하면 안 되는 영역 |


## source_position_feasibility_preview

이 폴더에는 이후 source-position 가능성을 검토하기 위해 만든 참고 이미지와 CSV가 있다.

```text
source_position_feasibility_preview/
  0727_contact_sheet.png
  0802_contact_sheet.png
  0804_contact_sheet.png
  0805_contact_sheet.png
  0811_contact_sheet.png
  0812_contact_sheet.png
  0813_contact_sheet.png
  source_position_feasibility.csv
  summary.json
```

이 자료는 현재 합성 결과 자체를 만들 때 사용한 주 파일은 아니고, asset의 원래 위치와 목표 도형 반대 위치가 얼마나 가까운지 검토하기 위한 참고 자료이다.

