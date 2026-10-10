# Public request examples

Read the section matching the selected Tool. These are format examples from
the qualified local cases, not assertions about a different workspace. Replace
scope IDs and source paths/owners with the task’s actual inputs. All requests
use `schema`, `scope`, and `sources`; optional operation fields vary. Source
categories retain their native meaning. An empty expected hash binds observed
bytes but does not verify an owner’s expected revision.

The outer Tool input is:

```json
{
  "path": ".",
  "patterns": [],
  "include_excluded": false,
  "request_json": "JSON string of the selected request below"
}
```

`patterns` selects acquisition files. Use the scope requested by the operator;
an empty list in these examples captures the selected example directory.

Raw byte retrieval and patch file bindings require an unprojected source
reference (`pointer` empty). Native Mdview retrieval records can bind an exact
JSON token and its original pointer/position.

## Request fields and examples

### evidence_inspect

```json
{
  "schema": "sessiontools.evidence_inspect.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "source",
      "path": "source.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "check",
      "path": "check.json",
      "owner": "selected-local-owner",
      "category": "local_check",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "mdview-compact",
      "path": "mdview-compact.json",
      "owner": "mdview",
      "category": "context_capture",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "query": ""
}
```

### evidence_source

```json
{
  "schema": "sessiontools.evidence_source.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "source",
      "path": "source.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "source_id": "source",
  "start_byte": 0,
  "end_byte": 74
}
```

### evidence_compare

```json
{
  "schema": "sessiontools.evidence_compare.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "before",
      "path": "before.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "current",
      "path": "current.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "after",
      "path": "after.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "bindings": [
    {
      "id": "unchanged",
      "owner": "selected-owner",
      "kind": "source",
      "before": "before",
      "after": "current"
    },
    {
      "id": "changed",
      "owner": "selected-owner",
      "kind": "test",
      "before": "before",
      "after": "after"
    }
  ],
  "evidence": [
    {
      "id": "proof-unchanged",
      "owner": "forge",
      "dependencies": [
        "unchanged"
      ],
      "closure_declared_complete": true,
      "verifier_reference": "forge owner proof"
    },
    {
      "id": "proof-affected",
      "owner": "forge",
      "dependencies": [
        "changed"
      ],
      "closure_declared_complete": true,
      "verifier_reference": "forge owner proof"
    },
    {
      "id": "unknown",
      "owner": "forge",
      "dependencies": [
        "unchanged"
      ],
      "closure_declared_complete": false,
      "verifier_reference": "forge owner proof"
    }
  ]
}
```

### provenance_trace

```json
{
  "schema": "sessiontools.provenance_trace.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "operations",
      "path": "operations.json",
      "owner": "semantic-work-history",
      "category": "operation_record",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "projection_source_id": "operations",
  "path": "/selected/a.go"
}
```

### patch_assess

```json
{
  "schema": "sessiontools.patch_assess.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "before",
      "path": "before.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "current",
      "path": "current.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "patch",
      "path": "patch.txt",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "baseline_name": "named-before",
  "current_name": "named-current",
  "baseline": [
    {
      "path": "value.go",
      "source_id": "before"
    }
  ],
  "current": [
    {
      "path": "value.go",
      "source_id": "current"
    }
  ],
  "patch_source_id": "patch",
  "selected_paths": [
    "value.go"
  ],
  "evidence": [
    {
      "id": "source-proof",
      "owner": "forge",
      "paths": [
        "value.go"
      ],
      "verifier_reference": "forge exact owner proof"
    }
  ],
  "required_checks": [
    "selected owner source checks"
  ]
}
```

### repository_observe

```json
{
  "schema": "sessiontools.repository_observe.v1",
  "scope": {
    "kind": "repository",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "inventory",
      "path": "inventory.json",
      "owner": "agent-orient",
      "category": "factory_diagnostic",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "inventory_source_id": "inventory"
}
```

### work_trace

```json
{
  "schema": "sessiontools.work_trace.v1",
  "scope": {
    "kind": "invocation",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "spans",
      "path": "spans.jsonl",
      "owner": "harness-sdk",
      "category": "work_span",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "span_source_id": "spans",
  "turn_id": "turn",
  "call_id": "call",
  "start": "2026-10-09T20:00:00Z",
  "end": "2026-10-09T20:00:02Z"
}
```

### composition_inspect

```json
{
  "schema": "sessiontools.composition_inspect.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "composition",
      "path": "composition.json",
      "owner": "forge",
      "category": "factory_diagnostic",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "diagnostic_source_id": "composition"
}
```

### factory_preflight

```json
{
  "schema": "sessiontools.factory_preflight.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "factory",
      "path": "factory.json",
      "owner": "forge",
      "category": "factory_diagnostic",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "diagnostic_source_id": "factory"
}
```

### specimen_prepare

```json
{
  "schema": "sessiontools.specimen_prepare.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "definition",
      "path": "specimen.json",
      "owner": "virtual-lab",
      "category": "lab_evidence",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "implementation",
      "path": "implementation.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "tests",
      "path": "test.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "definition_source_id": "definition"
}
```

### specimen_replay

```json
{
  "schema": "sessiontools.specimen_replay.v1",
  "scope": {
    "kind": "artifact",
    "id": "example-selected-scope"
  },
  "sources": [
    {
      "id": "definition",
      "path": "specimen.json",
      "owner": "virtual-lab",
      "category": "lab_evidence",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "implementation",
      "path": "implementation.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    },
    {
      "id": "tests",
      "path": "test.go",
      "owner": "selected-owner",
      "category": "source",
      "pointer": "",
      "expected_sha256": ""
    }
  ],
  "definition_source_id": "definition",
  "shrink_call_budget": 0
}
```
