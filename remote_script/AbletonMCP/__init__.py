# Live imports this package and calls create_instance. The surface import is
# deferred so the rest of the package stays importable outside Live (for tests).


def create_instance(c_instance):
    from .surface import AbletonMCPSurface

    return AbletonMCPSurface(c_instance)
