# ADR-0006 – Plugin API v2

**Status:** Accepted  
**Date:** 2026-03

## Context

FreeCAD's old addon mechanism relied on `__init__.py` being present in
`~/.FreeCAD/Mod/`.  There was no:

- Lifecycle contract (initialise / shutdown hooks)
- API version gating (addons silently broke on FreeCAD updates)
- Structured metadata (author, dependencies, minimum FreeCAD version)
- Error isolation (one bad addon could hang the startup sequence)

## Decision

Introduce a `PluginLifecycle` singleton (`src/App/PluginLifecycle.h/.cpp`):

```cpp
class AppExport PluginLifecycle {
public:
    static PluginLifecycle& instance();
    void loadPlugin(const PluginInfo& info);
    void unloadPlugin(const std::string& pluginId);
    void broadcastEvent(const PluginEvent& ev);
    const std::vector<PluginInfo>& loadedPlugins() const;
};
```

`PluginInfo` carries: `id`, `displayName`, `version`, `apiVersion`,
`entryModule`, `dependencies`.

`ApiVersion` uses SemVer comparison:

```cpp
struct ApiVersion { int major, minor, patch; bool isCompatible(ApiVersion required) const; };
```

Lifecycle hooks exposed to Python via `FreeCAD.PluginLifecycle`:

```python
class PluginBase:
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    def on_event(self, event: PluginEvent) -> None: ...
```

A `package.xml` schema (ROS2-compatible) provides structured metadata.
Addons lacking `package.xml` fall back to legacy loading with a deprecation
warning.

## Consequences

**Positive:**
- Addons declare the FreeCAD API version they require; incompatible addons
  skip gracefully rather than crashing.
- Clean `on_load` / `on_unload` allows addons to register/deregister
  resources deterministically.
- `broadcastEvent` enables inter-addon communication without tight coupling.

**Negative:**
- Existing addons must be updated to provide `package.xml` to avoid the
  deprecation warning.
- `PluginLifecycle` is a new singleton to maintain.
