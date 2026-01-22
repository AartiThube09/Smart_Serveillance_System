"""
Thin GUI shim that imports the existing GUI entry points from the single-file
application. This gives you a separate `gui.app_gui` module to import while
keeping the original implementation unchanged. If you'd like, I can move the
full GUI classes into this file in a follow-up.
"""
from complete_surveillance_system import main, AuthenticationWindow, SurveillanceApp

__all__ = ["main", "AuthenticationWindow", "SurveillanceApp"]

if __name__ == '__main__':
    main()
