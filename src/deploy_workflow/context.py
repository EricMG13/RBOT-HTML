"""Alias of ``deploy_vii.context``, where this module moved.

The engine layer, ``deploy_vii``, must not import this package (``.importlinter``). This name is
the same module object, so imports, monkeypatches and references through
``deploy_workflow.context`` keep working.
"""

import sys

from deploy_vii import context as _moved
from deploy_vii.context import *  # the public names, for type checkers

if __name__ == "__main__":  # python -m deploy_workflow.context
    sys.exit(_moved.main())
sys.modules[__name__] = _moved
