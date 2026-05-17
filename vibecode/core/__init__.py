__all__ = ["VibeCodeService"]


def __getattr__(name: str):
    if name == "VibeCodeService":
        from vibecode.core.memory_service import VibeCodeService

        return VibeCodeService
    raise AttributeError(name)
