"""raise RuntimeError('Deprecated: use config.settings.prod instead of epetcare.settings_production')
This module is deprecated.
It now simply imports from config.settings.prod to ease transition.
"""
from config.settings.prod import *  # noqa

# Add any backward compatibility shims here if needed