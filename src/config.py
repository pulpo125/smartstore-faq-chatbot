import os

import yaml
from easydict import EasyDict

# ==================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
# ==================================================

with open(os.path.join(PROJECT_ROOT, "conf/service.yaml")) as f:
    cfg = yaml.safe_load(f)

cfg = EasyDict(cfg)
