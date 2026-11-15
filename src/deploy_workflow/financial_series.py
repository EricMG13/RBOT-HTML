"""Alias of ``deploy_vii.financial_series``, where this module moved.

The engine layer, ``deploy_vii``, must not import this package (``.importlinter``). This name is
the same module object, so imports, monkeypatches and references through
``deploy_workflow.financial_series`` keep working.
"""

import sys

from deploy_vii import financial_series as _moved
from deploy_vii.financial_series import *  # the public names, for type checkers

sys.modules[__name__] = _moved
