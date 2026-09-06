"""pytest 配置：将 example/ 根目录加入 sys.path，使 demo_pkg 可被测试导入。"""

import sys
from pathlib import Path

EXAMPLE_ROOT = Path(__file__).resolve().parent
if str(EXAMPLE_ROOT) not in sys.path:
    sys.path.insert(0, str(EXAMPLE_ROOT))
