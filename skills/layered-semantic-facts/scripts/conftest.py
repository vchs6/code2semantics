"""scripts/ 测试树统一路径注入（覆盖 scripts 下全部组件测试，一处注入）。"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import layout  # noqa: E402

layout.register_skill_paths()  # scripts/ 经布局入口注册（组件包均在 scripts/ 下）
