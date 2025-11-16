# ShrutiMusic/utils/__init__.py
# Central utils package exports
# Preserve existing wildcard exports, and explicitly export commonly-needed helpers
# so that "from ShrutiMusic.utils import AdminRightsCheck, seconds_to_min" always works.

# (Keep project copyright header if needed)
from .channelplay import *
from .database import *
from .decorators import *
from .extraction import *
from .formatters import *
from .inline import *
from .pastebin import *
from .sys import *
from .error import *
from .couple import *

# Explicitly ensure AdminRightsCheck is exported from the utils package.
# Try the most likely module locations (decorators.admins, admins) and fall back safely.
try:
    # preferred: decorators.admins (we expect AdminRightsCheck in decorators/admins.py)
    from .decorators.admins import AdminRightsCheck, AdminActual, ActualAdminCB  # type: ignore
except Exception:
    try:
        # alternative location: utils/admins.py
        from .admins import AdminRightsCheck, AdminActual, ActualAdminCB  # type: ignore
    except Exception:
        AdminRightsCheck = None
        AdminActual = None
        ActualAdminCB = None

# Ensure seconds_to_min (or equivalent helper) is exported.
# Try to import from formatters; otherwise provide a small fallback.
try:
    from .formatters import seconds_to_min  # type: ignore
except Exception:
    def seconds_to_min(seconds):
        """Fallback: convert seconds to M:SS string or return original on error."""
        try:
            s = int(seconds)
            m, s = divmod(s, 60)
            return f"{m}:{s:02d}"
        except Exception:
            return str(seconds)

# Update __all__ to include these helpers explicitly
try:
    __all__  # if already defined by wildcard imports
except NameError:
    __all__ = []

for _name in ("AdminRightsCheck", "AdminActual", "ActualAdminCB", "seconds_to_min"):
    if _name not in __all__:
        __all__.append(_name)
