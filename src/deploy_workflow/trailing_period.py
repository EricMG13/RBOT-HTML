"""Alias of ``deploy_vii.trailing_period``, where this module moved.

The engine layer, ``deploy_vii``, must not import this package (``.importlinter``). This name is
the same module object, so imports, monkeypatches and references through
``deploy_workflow.trailing_period`` keep working.
"""

import sys

from deploy_vii import trailing_period as _moved
from deploy_vii.trailing_period import *  # the public names, for type checkers

sys.modules[__name__] = _moved
