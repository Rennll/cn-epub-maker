# Configuration Resolver API Compatibility Notes

This document records implementation-level compatibility notes for the Configuration Resolver API. It is intentionally separate from the deferred-decision audit: these notes do not introduce a new configuration-layer decision or reopen the resolved configuration model.

## `values` versus `cli` precedence

The resolver currently retains the positional `values` input for compatibility with existing callers. When both `values` and the named `cli` layer are supplied, `values` has higher precedence than `cli`.

The documented three-layer configuration model remains:

```text
application_defaults < config_file < cli
```

The higher precedence of `values` is therefore a compatibility behavior of the current API, not an additional configuration layer or a change to the architectural precedence model.

### Follow-up condition

If a future caller needs to provide both `values` and `cli`, revisit the API before adding more call sites. Consider clarifying the semantic role or name of `values`, or removing the compatibility path, rather than silently changing its precedence.
