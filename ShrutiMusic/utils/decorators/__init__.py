# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com
#
# This file exposes decorator helpers for the project. It will:
# - Attempt to import ONLY_ADMIN and ONLY_GROUP from likely submodules
#   (admins, language, or other decorator modules).
# - If not found, provide safe no-op fallback decorators so imports don't fail.
# - Preserve existing wildcard re-exports from submodules (admins, language).
#
# Place this file at: ShrutiMusic/utils/decorators/__init__.py

from __future__ import annotations

import importlib
import warnings
from typing import Callable, Optional, Any

# Preserve original wildcard exports if modules exist
# (these imports are safe: if a module doesn't exist, import will be skipped)
try:
    from .admins import *  # noqa: F401,F403
except Exception:
    # admins module missing or failing import; continue with compatibility shim
    pass

try:
    from .language import *  # noqa: F401,F403
except Exception:
    pass

__all__ = [
    # explicit decorator exports (populated below)
    "ONLY_ADMIN",
    "ONLY_GROUP",
    # keep room for other wildcard exports if present in submodules
]

# Candidate modules to search for real decorator implementations.
_CANDIDATES = (
    "ShrutiMusic.utils.decorators.admins",
    "ShrutiMusic.utils.decorators.admin",
    "ShrutiMusic.utils.decorators.auth",
    "ShrutiMusic.utils.decorators.only",
    "ShrutiMusic.utils.decorators.core",
    "ShrutiMusic.utils.decorators",
)

def _try_import_real():
    for mod_name in _CANDIDATES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        only_admin = getattr(mod, "ONLY_ADMIN", None)
        only_group = getattr(mod, "ONLY_GROUP", None)
        if only_admin is not None and only_group is not None:
            return only_admin, only_group
    return None, None


ONLY_ADMIN, ONLY_GROUP = _try_import_real()

if ONLY_ADMIN is None or ONLY_GROUP is None:
    warnings.warn(
        "ShrutiMusic.utils.decorators: ONLY_ADMIN/ONLY_GROUP not found in submodules. "
        "Using no-op placeholders. Replace with real implementations when available.",
        RuntimeWarning,
    )

    def _make_noop_decorator():
        """
        Return a decorator that is safe to use as:
          @ONLY_ADMIN
        or:
          @ONLY_ADMIN()
        or with optional keyword args: @ONLY_ADMIN(foo=True)

        The decorator returns the original function unchanged.
        Works with sync or async functions.
        """
        def outer(*d_args: Any, **d_kwargs: Any):
            # Used as @ONLY_ADMIN (no parentheses)
            if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
                func = d_args[0]

                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            # Used as @ONLY_ADMIN() or @ONLY_ADMIN(...params)
            def _decorator(func: Callable):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                return wrapper

            return _decorator

        return outer

    ONLY_ADMIN = _make_noop_decorator()
    ONLY_GROUP = _make_noop_decorator()

# Ensure exports include any names imported with wildcard earlier
try:
    # extend __all__ with attributes from admins/language if they were imported
    for name in list(globals().keys()):
        if name.isupper() and name not in __all__:
            __all__.append(name)
except Exception:
    pass
