import importlib
import warnings
from typing import Callable, Any, Optional

__all__ = ["ONLY_ADMIN", "ONLY_GROUP"]

# Try to import from likely submodule
_only_admin = None
_only_group = None

_candidates = (
    "ShrutiMusic.utils.decorators.admins",
    "ShrutiMusic.utils.decorators.admin",
    "ShrutiMusic.utils.decorators.auth",
    "ShrutiMusic.utils.decorators",
)

for mod in _candidates:
    try:
        m = importlib.import_module(mod)
    except Exception:
        continue
    _only_admin = getattr(m, "ONLY_ADMIN", _only_admin)
    _only_group = getattr(m, "ONLY_GROUP", _only_group)
    if _only_admin and _only_group:
        break

if _only_admin is not None and _only_group is not None:
    ONLY_ADMIN, ONLY_GROUP = _only_admin, _only_group
else:
    warnings.warn(
        "ShrutiMusic.utils.decorators: ONLY_ADMIN/ONLY_GROUP not found. Using no-op placeholders.",
        RuntimeWarning,
    )

    def _make_noop_decorator():
        def outer(*d_args: Any, **d_kwargs: Any):
            if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
                func = d_args[0]
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper
            def decorator(func: Callable):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper
            return decorator
        return outer

    ONLY_ADMIN = _make_noop_decorator()
    ONLY_GROUP = _make_noop_decorator()
