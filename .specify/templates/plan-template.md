# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11 (REQUIRED if Python used), Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Web (Chrome/Edge/Firefox/Safari 90+) + Mobile (iOS 15+, Android 7.0+) or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Review compliance with `.specify/memory/constitution.md`:

1. **Cross-Platform Readiness**: Does the design support web and mobile?
2. **Windows Compatibility**: Can all build/test steps run on Windows?
3. **Port Management**: Are port conflicts handled gracefully?
4. **GPU Acceleration**: If AI models are used, is GPU enabled by default?
5. **MCP Integration**: Are Context7 and ChromeDevTools utilized appropriately?
6. **Test Coverage**: Are tests written and approved before implementation?
7. **Observability**: Is structured logging and error tracing included?
8. **Dependency Stability**: Are all dependencies stable versions with verified compatibility?
9. **Simplicity**: Is the code simple, clear, and maintainable?
10. **Complete Examples**: Are all code examples complete and runnable?
11. **Modular Design**: Is the architecture modular with clear boundaries?
12. **CI Integration**: Are CI checks configured and passing?
13. **Milestone Versioning**: Are significant achievements committed and tagged in GitHub?

| Check | Status | Notes |
|-------|--------|-------|
| Cross-Platform | ⚠️/✅/❌ | [Explain web/mobile support] |
| Windows Compat | ⚠️/✅/❌ | [Explain Windows compatibility] |
| Port Management | ⚠️/✅/❌ | [Explain port handling strategy] |
| GPU Acceleration | ⚠️/✅/❌/N/A | [Explain GPU usage if AI models present] |
| MCP Integration | ⚠️/✅/❌ | [Explain Context7/ChromeDevTools usage] |
| Test Coverage | ⚠️/✅/❌ | [Explain test-first approach] |
| Observability | ⚠️/✅/❌ | [Explain logging/tracing strategy] |
| Dependency Stability | ⚠️/✅/❌ | [Explain dependency versions and compatibility checks] |
| Simplicity | ⚠️/✅/❌ | [Explain code simplicity and clarity approach] |
| Complete Examples | ⚠️/✅/❌ | [Explain documentation with full code examples] |
| Modular Design | ⚠️/✅/❌ | [Explain modular architecture and boundaries] |
| CI Integration | ⚠️/✅/❌ | [Explain CI/CD pipeline configuration] |
| Milestone Versioning | ⚠️/✅/❌ | [Explain git tagging strategy for milestones] |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
