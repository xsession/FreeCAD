# ADR-0007 – Dual-layer PDM provider ABC

**Status:** Accepted  
**Date:** 2026-03

## Context

FreeCAD targets professional engineering teams that use PDM/PLM systems
(Windchill, ENOVIA, Vault, …) for revision control.  There was no extension
point for third parties to plug in check-in/check-out behaviour.

A C++-only interface (`App::PdmProvider`) was sketched but:

- Python-heavy shops cannot implement it without writing a C++ extension.
- There was no module-registration mechanism; each provider needed to patch
  `Application` itself.

## Decision

Two-layer design:

### Layer 1 — C++ pure interface (`src/App/PdmProvider.h`)

```cpp
class AppExport PdmProvider {
public:
    virtual ~PdmProvider() = default;
    virtual std::string name() const = 0;
    virtual bool checkOut(Document* doc) = 0;
    virtual bool checkIn(Document* doc, const std::string& comment) = 0;
    ...
};
```

Registered on the `Application` singleton via
`Application::setPdmProviderPy()` / `Application::getPdmProviderPy()`.

### Layer 2 — Python ABC (`src/App/PdmProviderPy.py`)

```python
class PdmProviderBase(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str: ...
    @abc.abstractmethod
    def check_out(self, doc_path: str) -> bool: ...
    @abc.abstractmethod
    def check_in(self, doc_path: str, comment: str) -> bool: ...
    ...

def set_active_provider(provider: PdmProviderBase) -> None: ...
def get_active_provider() -> Optional[PdmProviderBase]: ...
```

Exposed to FreeCAD Python API as:

```python
FreeCAD.setActivePdmProvider(provider)
FreeCAD.getActivePdmProvider() -> provider | None
```

## Consequences

**Positive:**
- Python shops can implement PDM integration without any C++ knowledge.
- `abc.abstractmethod` gives early, clear error messages when methods are
  missing.
- The `PdmRevision` dataclass is serialisable (dataclasses.asdict()).

**Negative:**
- Two layers to keep semantically in sync (C++ + Python ABCs).
- Python provider calls must acquire the GIL; not suitable for hot paths.
