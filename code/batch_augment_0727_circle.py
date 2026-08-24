from __future__ import annotations

"""과거 circle 전용 명령과의 호환을 위한 wrapper.

현재 최종 0802~0805 결과 생성에는 사용하지 않는다.
"""

import sys
from pathlib import Path

from batch_augment_0727 import main


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    if "--target" not in sys.argv:
        sys.argv.extend(["--target", "circle"])
    if "--output-root" not in sys.argv:
        sys.argv.extend(["--output-root", str(project_root / "outputs" / "0727_erase_circle_shape_aug")])
    raise SystemExit(main())
