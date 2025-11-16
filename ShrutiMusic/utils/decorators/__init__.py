# ShrutiMusic/utils/decorators/__init__.py
# Compatibility entrypoint for decorator helpers.
# Tries to use real implementations from .admins (or other likely modules).
# If not found, supplies async-aware no-op fallbacks.

from __future__ import annotations

import importlib
import inspect
import warnings
from functools import wraps
from typing import Any, Callable, Optional

# Try to preserve wildcard exports if submodules exist
try:
    from .admins import *  # noqa: F401,F403
except Exception:
    pass

try:
    from .language import *  # noqa: F401,F403
except Exception:
    pass

__all__ = [
    "ONLY_ADMIN",
    "ONLY_GROUP",
]

# Safe async-aware no-op decorator factory
def _make_safe_noop_decorator():
    """
    Returns a decorator usable as:
      @ONLY_ADMIN
    or:
      @ONLY_ADMIN()
    Works with sync and async functions. The returned wrappers are async
    so they are safe to be awaited by the framework (Pyrogram).
    """
    def outer(*d_args: Any, **d_kwargs: Any):
        # Used as @DECORATOR without parentheses
        if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
            func = d_args[0]
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def _async_wr(*args, **kwargs):
                    return await func(*args, **kwargs)
                return _async_wr
            else:
                @wraps(func)
                async def _sync_wr(*args, **kwargs):
                    return func(*args, **kwargs)
                return _sync_wr

        # Used as @DECORATOR() or @DECORATOR(...params)
        def _decorator(func: Callable):
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def _inner_async(*args, **kwargs):
                    return await func(*args, **kwargs)
                return _inner_async
            else:
                @wraps(func)
                async def _inner_sync(*args, **kwargs):
                    return func(*args, **kwargs)
                return _inner_sync

        return _decorator

    return outer

# Attempt to load real decorators from common locations
_ONLY_ADMIN: Optional[Callable] = None
_ONLY_GROUP: Optional[Callable] = None

_candidates = (
    "ShrutiMusic.utils.decorators.admins",
    "ShrutiMusic.utils.decorators.admin",
    "ShrutiMusic.utils.decorators.auth",
    "ShrutiMusic.utils.decorators.only",
    "ShrutiMusic.utils.decorators.core",
    "ShrutiMusic.utils.decorators",
)

for mod_name in _candidates:
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        continue

    # If module provides explicit names, use them
    if hasattr(mod, "ONLY_ADMIN"):
        _ONLY_ADMIN = getattr(mod, "ONLY_ADMIN")
    if hasattr(mod, "ONLY_GROUP"):
        _ONLY_GROUP = getattr(mod, "ONLY_GROUP")

    # If explicit names not present, map common decorator names from admins.py
    if _ONLY_ADMIN is None and hasattr(mod, "AdminRightsCheck"):
        _ONLY_ADMIN = getattr(mod, "AdminRightsCheck")
    if _ONLY_GROUP is None and hasattr(mod, "AdminActual"):
        _ONLY_GROUP = getattr(mod, "AdminActual")

    # If both found, stop searching
    if _ONLY_ADMIN is not None and _ONLY_GROUP is not None:
        break

# If still not found, use safe fallbacks and warn in logs
if _ONLY_ADMIN is None or _ONLY_GROUP is None:
    warnings.warn(
        "ShrutiMusic.utils.decorators: ONLY_ADMIN/ONLY_GROUP not found in decorators submodules. "
        "Using async-aware no-op placeholders. Replace with real implementations if available.",
        RuntimeWarning,
    )
    ONLY_ADMIN = _make_safe_noop_decorator()
    ONLY_GROUP = _make_safe_noop_decorator()
else:
    ONLY_ADMIN = _ONLY_ADMIN
    ONLY_GROUP = _ONLY_GROUP

# Ensure exports are accurate
__all__ = list(dict.fromkeys(__all__ + [name for name in ("ONLY_ADMIN", "ONLY_GROUP") if name]))
