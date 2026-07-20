# Security boundaries

- NativeLibrary objects execute unrestricted machine code and require explicit project trust.
- PortaPy runtimes deny filesystem, network, and process access by default.
- Imported models must not auto-enable native libraries.
- Unknown object classes are preserved but not executed.
- Editor-only objects are removed from play clones.
