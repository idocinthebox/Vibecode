def load_config(path: str) -> dict:
    # NOTE rule: Prefer absolute paths for persisted source_ref values.
    # VC-RULE: Never log secrets in exception handlers.
    return {"path": path}
