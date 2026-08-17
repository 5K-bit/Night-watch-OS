# Changelog

## 0.2.0

- define Nightwatch as the OBEOS operator-runtime component
- add a supported `NightwatchClient` HTTP integration boundary
- harden SQLite with WAL, foreign keys, busy timeouts, and connection health checks
- create parent directories for custom database paths and validate configured ports
- reject blank task titles after whitespace normalization
- make network telemetry local-first instead of depending on public internet reachability
- add integration and regression tests for task validation, network detection, and the client boundary
