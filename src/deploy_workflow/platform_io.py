"""Alias of ``deploy_vii.platform_io``, where this module moved.

The engine layer, ``deploy_vii``, must not import this package (``.importlinter``). This name is
the same module object, so imports, monkeypatches and references through
``deploy_workflow.platform_io`` keep working.
"""

import sys

from deploy_vii import platform_io as _moved
from deploy_vii.platform_io import *  # the public names, for type checkers

sys.modules[__name__] = _moved
