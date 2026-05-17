__all__ = [
    "get_service_settings",
    "get_vibecode_dir",
    "get_vibecode_logs_dir",
    "ServiceSettings",
]


def __getattr__(name: str):
    if name in {"get_vibecode_dir", "get_vibecode_logs_dir"}:
        from vibecode.config.paths import get_vibecode_dir, get_vibecode_logs_dir

        return {
            "get_vibecode_dir": get_vibecode_dir,
            "get_vibecode_logs_dir": get_vibecode_logs_dir,
        }[name]
    if name in {"ServiceSettings", "get_service_settings"}:
        from vibecode.config.settings import ServiceSettings, get_service_settings

        return {
            "ServiceSettings": ServiceSettings,
            "get_service_settings": get_service_settings,
        }[name]
    raise AttributeError(name)
