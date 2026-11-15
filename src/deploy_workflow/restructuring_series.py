"""Alias of ``deploy_vii.restructuring_series``, where this module moved.

The engine layer, ``deploy_vii``, must not import this package (``.importlinter``). This name is
the same module object, so imports, monkeypatches and references through
``deploy_workflow.restructuring_series`` keep working.
"""

import sys

from deploy_vii import restructuring_series as _moved
from deploy_vii.restructuring_series import *  # the public names, for type checkers

sys.modules[__name__] = _moved
