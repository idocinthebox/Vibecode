# Failure Bank

## Do not mix PyQt5 and PySide6
- **ID:** 120b7ee6-582c-4e04-a492-3798aa5d7ea8
- **Severity:** high
- **Bad Suggestion:** Mix Qt bindings
- **Why It Failed:** Causes packaging conflicts
- **Prevention Rule:** Do not reintroduce PyQt5 when PySide6 is used
- **Corrected Approach:** Use only PySide6
- **Tags:** qt, packaging
