__all__ = [
    "CaptureService",
    "ExportService",
    "HashService",
    "InjectionService",
    "MigrationService",
    "SearchService",
    "TokenService",
]


def __getattr__(name: str):
    if name == "CaptureService":
        from vibecode.services.capture_service import CaptureService

        return CaptureService
    if name == "ExportService":
        from vibecode.services.export_service import ExportService

        return ExportService
    if name == "HashService":
        from vibecode.services.hash_service import HashService

        return HashService
    if name == "InjectionService":
        from vibecode.services.injection_service import InjectionService

        return InjectionService
    if name == "MigrationService":
        from vibecode.services.migration_service import MigrationService

        return MigrationService
    if name == "SearchService":
        from vibecode.services.search_service import SearchService

        return SearchService
    if name == "TokenService":
        from vibecode.services.token_service import TokenService

        return TokenService
    raise AttributeError(name)
