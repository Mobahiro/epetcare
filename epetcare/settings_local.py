"""raise RuntimeError('Deprecated: use config.settings.dev instead of epetcare.settings_local')

This module is deprecated.

It now simply imports from config.settings.dev to ease transition.
"""
from config.settings.dev import *  # noqa

# Add any backward compatibility shims here if needed