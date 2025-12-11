<!--
  Sync Impact Report (2025-12-04)
  ================================
  Version Change: 1.2.0 → 1.3.0
  Amendment Type: MINOR (new principle added)

  Modified Principles:
  - None (no existing principles changed)

  Added Principles:
  - XIII. Milestone Version Control

  Removed Principles:
  - None

  Added Sections:
  - New principle XIII in Core Principles section

  Removed Sections:
  - None

  Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section updated to include version control milestone
  ✅ spec-template.md - Already aligned (requirements include deliverables)
  ✅ tasks-template.md - Already includes git/version control tasks
  ✅ checklist-template.md - No dependencies (template-agnostic)

  Follow-up TODOs:
  - None - all placeholders filled with concrete values

  Notes:
  - Original ratification date preserved: 2025-12-04
  - Last amended date updated: 2025-12-04 (same day amendment)
  - Version bumped to 1.3.0 (MINOR) - new principle added without breaking existing governance
  - New principle emphasizes GitHub-based milestone versioning for major achievements
  - Compliance Review checklist updated to include 13 principles (I-XIII)
-->

# KidComic Constitution

## Core Principles

### I. Cross-Platform Production Ready

The application MUST be production-ready for both web and mobile device platforms.

**Rationale**: Multi-platform delivery ensures maximum user reach and engagement. Production readiness means code meets quality, performance, and security standards before deployment.

**Non-negotiable rules**:
- All features MUST work on web browsers (desktop and mobile viewports)
- All features MUST work on native mobile devices (iOS/Android)
- Platform-specific optimizations MUST NOT break cross-platform compatibility
- Production builds MUST pass all quality gates before deployment

### II. Windows Environment Optimization

All development, testing, and build processes MUST be optimized for Windows PC environments.

**Rationale**: Development occurs on Windows machines. Tooling, scripts, and workflows must be Windows-compatible to ensure developer productivity and consistent build outputs.

**Non-negotiable rules**:
- File paths MUST use Windows-compatible separators or cross-platform libraries
- Scripts MUST run on Windows (PowerShell, CMD, or cross-platform tools like Node.js)
- Dependencies MUST support Windows installation (no Unix-only packages without WSL fallback documented)
- Build processes MUST execute successfully on Windows without manual workarounds

### III. Port Management

All services and development servers MUST check for port availability before assignment to prevent conflicts.

**Rationale**: Port conflicts cause cryptic failures and waste developer time. Proactive port checking ensures services start reliably and fail fast with clear error messages if ports are unavailable.

**Non-negotiable rules**:
- Services MUST attempt to detect if their target port is in use before binding
- If a port is occupied, the service MUST either:
  - Log a clear error message indicating the port and process using it, OR
  - Automatically select an available port and log the chosen port
- Port configuration MUST be environment-variable driven (not hardcoded)
- Documentation MUST list all default ports used by the application

### IV. AI Model GPU Acceleration

When AI models are used, GPU acceleration MUST be enabled by default.

**Rationale**: AI/ML workloads are computationally intensive. GPU acceleration provides orders-of-magnitude performance improvements, reducing latency and enabling real-time user experiences.

**Non-negotiable rules**:
- AI model initialization MUST detect GPU availability and enable it by default
- If GPU is unavailable, system MUST log a warning and gracefully fall back to CPU
- Model loading logic MUST specify device placement explicitly (e.g., `device='cuda'`, `device='mps'`, or `device='cpu'`)
- Performance benchmarks MUST document GPU vs. CPU performance differences

### V. Context7 & ChromeDevTools Integration

The project MUST utilize Context7 for documentation retrieval and ChromeDevTools MCP server for browser automation/testing where applicable.

**Rationale**: Context7 provides up-to-date library documentation, reducing context switching and outdated reference usage. ChromeDevTools enables reliable end-to-end testing and debugging of web interfaces.

**Non-negotiable rules**:
- When researching libraries or APIs, Context7 MUST be queried for current documentation
- Web UI testing MUST leverage ChromeDevTools MCP for automated browser interactions
- MCP tool usage MUST be logged for debugging and audit purposes
- Fallback strategies MUST exist if MCP tools are unavailable (manual steps documented)

### VI. Test-First Development

Tests MUST be written before implementation, approved by stakeholders, and verified to fail before code is written.

**Rationale**: Test-Driven Development ensures requirements are clear, testable, and met. Red-Green-Refactor cycle prevents untested code and reduces regressions.

**Non-negotiable rules**:
- For each user story or feature, acceptance tests MUST be written first
- Tests MUST be reviewed and approved before implementation begins
- Tests MUST fail initially (red phase) to confirm they are valid
- Implementation proceeds only after test failure is confirmed (green phase)
- Refactoring MUST NOT break passing tests

### VII. Observability & Debugging

All components MUST provide structured logging, error tracing, and runtime introspection capabilities.

**Rationale**: Production systems require visibility into runtime behavior for debugging, performance tuning, and incident response. Structured logs enable automated analysis and alerting.

**Non-negotiable rules**:
- All services MUST emit structured logs (JSON or key-value format preferred)
- Log levels MUST be configurable via environment variables (DEBUG, INFO, WARN, ERROR)
- Errors MUST include stack traces, request IDs, and contextual metadata
- Performance-critical paths MUST include timing instrumentation

### VIII. Stable Dependencies & Compatibility

All project dependencies MUST use stable versions, and cross-dependency compatibility MUST be verified before installation.

**Rationale**: Unstable or pre-release dependencies introduce unpredictable bugs, security vulnerabilities, and breaking changes. Incompatible dependency versions cause runtime failures, build breakages, and wasted developer time. Stable, compatible dependencies ensure reliable builds and predictable behavior.

**Non-negotiable rules**:
- Dependencies MUST use stable releases (no alpha, beta, rc, or dev versions in production)
- Pre-release versions MAY be used only in dedicated testing/staging environments with explicit documentation
- Before adding or upgrading dependencies, compatibility MUST be verified:
  - Check peer dependency requirements (e.g., npm peer dependencies, Python package constraints)
  - Verify version range compatibility across all direct and transitive dependencies
  - Test dependency installation in a clean environment to detect conflicts early
- Dependency conflicts MUST be resolved before merging:
  - Document resolution strategy (upgrade, downgrade, alternative package)
  - Verify all affected functionality still works after conflict resolution
- Lockfiles (package-lock.json, yarn.lock, requirements.txt, Pipfile.lock, etc.) MUST be committed and kept up-to-date
- Automated dependency scanning tools (e.g., npm audit, pip check, Dependabot) MUST run in CI/CD pipelines

### IX. Simplicity & Clarity

Code MUST prioritize simplicity, readability, and clarity over cleverness or premature optimization.

**Rationale**: Simple code is easier to understand, maintain, debug, and extend. Complex code increases cognitive load, introduces bugs, and slows development. Clear code reduces onboarding time and enables confident refactoring.

**Non-negotiable rules**:
- Functions MUST do one thing and do it well (Single Responsibility Principle)
- Variable and function names MUST be descriptive and self-documenting (avoid abbreviations unless industry-standard)
- Cyclomatic complexity MUST be kept low (prefer <10, flag >15 for review)
- Nested logic MUST be minimized (prefer early returns, guard clauses, and extracted functions)
- "Clever" solutions MUST be avoided unless performance-critical and well-documented
- Code MUST be written for humans first, machines second

**Example - Prefer Simple Over Clever**:
```python
# ❌ BAD: Clever but unclear
result = [x for x in data if (lambda y: y%2==0 and y>10)(x)]

# ✅ GOOD: Simple and clear
def is_valid_number(num):
    return num > 10 and num % 2 == 0

result = [num for num in data if is_valid_number(num)]
```

### X. Complete Code Examples

All documentation, code reviews, and technical proposals MUST include complete, runnable code examples.

**Rationale**: Partial code snippets lead to misunderstandings, implementation errors, and wasted time. Complete examples demonstrate correct usage, edge cases, and integration patterns. They serve as living documentation and reduce back-and-forth clarifications.

**Non-negotiable rules**:
- Code examples MUST be complete and runnable without modification
- Examples MUST include all necessary imports, setup, and error handling
- Examples MUST demonstrate typical usage patterns, not just happy paths
- Examples MUST include input data and expected output where applicable
- API documentation MUST include end-to-end examples showing request/response cycles
- Complex features MUST include step-by-step implementation guides with full code

**Example - Complete Code Example**:
```python
# ✅ GOOD: Complete, runnable example
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_user_data(user_id: str, data: dict) -> dict:
    """
    Process user data with validation and error handling.

    Args:
        user_id: Unique user identifier
        data: User data dictionary with 'name' and 'email' keys

    Returns:
        Processed data with timestamp

    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    if not user_id or not isinstance(user_id, str):
        raise ValueError("user_id must be a non-empty string")

    required_fields = ['name', 'email']
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    # Process data
    processed = {
        'user_id': user_id,
        'name': data['name'].strip(),
        'email': data['email'].lower().strip(),
        'processed_at': datetime.utcnow().isoformat()
    }

    logger.info(f"Processed data for user {user_id}")
    return processed

# Example usage
if __name__ == "__main__":
    # Happy path
    user_data = {'name': 'John Doe', 'email': 'JOHN@EXAMPLE.COM'}
    result = process_user_data('user123', user_data)
    print(f"Success: {result}")

    # Error case
    try:
        invalid_data = {'name': 'Jane'}  # Missing email
        process_user_data('user456', invalid_data)
    except ValueError as e:
        print(f"Validation failed: {e}")
```

### XI. Modular Architecture

Code MUST be organized into independent, reusable modules with clear boundaries and minimal coupling.

**Rationale**: Modular architecture enables parallel development, easier testing, code reuse, and independent deployment. Tight coupling creates fragile systems where changes cascade unpredictably. Clear module boundaries improve maintainability and reduce cognitive load.

**Non-negotiable rules**:
- Modules MUST have single, well-defined purposes (high cohesion)
- Modules MUST depend on abstractions, not concrete implementations (Dependency Inversion)
- Module interfaces MUST be stable and versioned (breaking changes require major version bump)
- Modules MUST be independently testable without requiring full system setup
- Shared code MUST be extracted into reusable libraries or utilities
- Circular dependencies between modules MUST be eliminated

**Example - Modular Structure**:
```
# ✅ GOOD: Clear modular separation
src/
├── core/               # Core business logic (no external dependencies)
│   ├── models.py       # Data models
│   ├── validators.py   # Validation logic
│   └── processors.py   # Business operations
├── adapters/           # External integrations (adapters pattern)
│   ├── database.py     # Database adapter
│   ├── api_client.py   # External API client
│   └── storage.py      # File/object storage
├── services/           # Application services (orchestration)
│   ├── user_service.py
│   └── auth_service.py
└── interfaces/         # External interfaces (REST, CLI, etc.)
    ├── api/            # REST API
    └── cli/            # Command-line interface

# Each module has clear dependencies:
# interfaces → services → core ← adapters
# (interfaces and adapters never depend on each other)
```

### XII. Continuous Integration

All code changes MUST pass automated CI/CD pipelines before merging, ensuring consistent quality and rapid feedback.

**Rationale**: Manual testing is error-prone, slow, and non-repeatable. Automated CI catches issues early, enforces standards, and enables confident refactoring. Fast feedback loops accelerate development and reduce context switching.

**Non-negotiable rules**:
- All commits to main/master branch MUST trigger CI builds
- CI pipelines MUST complete within 10 minutes (optimize or parallelize if slower)
- CI MUST include at minimum:
  - Linting and code formatting checks
  - Unit tests with coverage reporting
  - Integration tests for critical paths
  - Dependency security scanning
  - Build verification for all target platforms
- Failed CI checks MUST block pull request merging (no manual overrides without documented justification)
- Main/master branch MUST always be in a deployable state (green builds only)
- CI failures MUST be fixed within 1 business day or reverted
- Flaky tests MUST be fixed or disabled (never ignored)

**Example - CI Pipeline Configuration** (GitHub Actions):
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: windows-latest  # Windows environment per Principle II
    strategy:
      matrix:
        python-version: ['3.11']  # Python 3.11 per Technical Standards

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint with flake8
      run: |
        flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ --count --max-complexity=10 --max-line-length=100 --statistics

    - name: Format check with black
      run: black --check src/

    - name: Type check with mypy
      run: mypy src/

    - name: Security check
      run: |
        pip install safety
        safety check --json

    - name: Run unit tests with coverage
      run: |
        pytest tests/unit --cov=src --cov-report=xml --cov-report=term

    - name: Run integration tests
      run: pytest tests/integration

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true

  build:
    runs-on: windows-latest
    needs: test

    steps:
    - uses: actions/checkout@v3

    - name: Build for web
      run: npm run build:web

    - name: Build for mobile
      run: npm run build:mobile

    - name: Verify build artifacts
      run: |
        Test-Path dist/web/index.html
        Test-Path dist/mobile/app.apk
```

### XIII. Milestone Version Control

Every significant milestone or achievement MUST be committed and pushed to GitHub with a tagged version.

**Rationale**: Version control provides a safety net for experimentation, enables collaboration, and creates a recoverable history. Milestone tagging marks significant progress points, enabling rollback to known-good states and tracking project evolution. GitHub serves as both backup and collaboration platform.

**Non-negotiable rules**:
- All milestone achievements MUST be committed to git with descriptive commit messages
- Milestone commits MUST be pushed to GitHub remote repository (not just local)
- Significant milestones MUST be tagged with semantic version numbers (e.g., v0.1.0, v0.2.0, v1.0.0)
- Tags MUST follow semantic versioning for milestone significance:
  - **MAJOR (v1.0.0, v2.0.0)**: Complete feature delivered, production-ready, or breaking changes
  - **MINOR (v0.1.0, v0.2.0)**: Major functionality working end-to-end, significant progress
  - **PATCH (v0.1.1, v0.1.2)**: Bug fixes, minor improvements to existing milestone
- Commit messages MUST describe what was achieved, not just what was changed
- Working code at end of day MUST be committed (even if incomplete feature)
- Before risky changes (major refactor, architecture changes), MUST commit current working state

**What qualifies as a "milestone"**:
- ✅ First feature working end-to-end (e.g., "User login works on web")
- ✅ Platform support added (e.g., "Mobile version now works")
- ✅ Major integration complete (e.g., "Database connected and CRUD operations work")
- ✅ Performance improvement achieved (e.g., "Page load time reduced from 5s to 1s")
- ✅ All tests passing after major work
- ✅ Ready for demo/review/deployment
- ✅ Before starting risky or complex changes

**Example - Milestone Commit and Tag Workflow**:
```bash
# 1. Commit your milestone achievement
git add .
git commit -m "feat: implement user authentication with email/password

- Add login/signup forms (web and mobile)
- Implement JWT token generation and validation
- Add password hashing with bcrypt
- Create user session management
- All authentication tests passing

Milestone: Core authentication system complete and working"

# 2. Push to GitHub
git push origin main

# 3. Tag the milestone
git tag -a v0.2.0 -m "Milestone v0.2.0: User authentication system complete

Features:
- User registration with email validation
- Secure login with JWT tokens
- Password reset flow
- Session management
- Works on both web and mobile platforms

This milestone delivers a production-ready authentication system."

# 4. Push the tag to GitHub
git push origin v0.2.0

# 5. Verify on GitHub
# Navigate to https://github.com/your-username/your-repo/releases
# You should see your tagged release with the description
```

**Example - Daily Commit Workflow** (End of Day):
```bash
# Even if feature isn't complete, commit working state
git add .
git commit -m "wip: user profile page UI (70% complete)

Completed:
- Profile form layout for web
- Avatar upload component
- Form validation logic

TODO:
- Mobile responsive layout
- Backend API integration
- Error handling for network failures

Note: Code compiles and existing features still work"

git push origin main
```

**Example - Pre-Risk Commit** (Before Major Refactoring):
```bash
# Save known-good state before risky changes
git add .
git commit -m "checkpoint: stable state before refactoring authentication

Current state: All features working, all tests passing.

About to refactor:
- Extract authentication logic to separate service
- Migrate from session-based to token-based auth
- Update all API endpoints to use new auth pattern

Creating checkpoint to enable easy rollback if refactor fails."

git push origin main
git tag -a v0.1.5-stable -m "Stable checkpoint before authentication refactor"
git push origin v0.1.5-stable
```

**GitHub Best Practices**:
- Repository MUST have a descriptive README.md explaining what the project does
- Commits MUST be pushed at least daily (never lose more than 1 day of work)
- Use meaningful branch names for experimental features (e.g., `feature/payment-integration`)
- Main/master branch MUST always contain working code (use branches for broken/incomplete work)
- GitHub Issues SHOULD be used to track known bugs and planned features
- Pull Requests SHOULD be used for code review (even for solo projects, good habit)

## Technical Standards

### Platform & Dependency Requirements

**Python Version**: When Python is used, version 3.11 MUST be the target runtime.

**Rationale**: Python 3.11 provides significant performance improvements and is the standard version for this project.

**Mobile Platforms**: Applications MUST support iOS 15+ and Android API 24+ (Android 7.0) minimum.

**Web Browsers**: Applications MUST support:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Safari (iOS 15+)
- Chrome Mobile (Android 7.0+)

**Dependency Management**:
- All dependencies MUST be version-pinned in lockfiles (requirements.txt, package-lock.json, etc.)
- Major version upgrades MUST be tested in isolation before merging
- Security vulnerabilities MUST be addressed within 7 days of disclosure

## Quality Gates

### Constitution Compliance Check

Before Phase 0 research and after Phase 1 design, all features MUST verify compliance with:

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

**Violations** MUST be documented in the `Complexity Tracking` section of plan.md with explicit justification.

### Testing Standards

- **Unit Tests**: All business logic functions MUST have unit tests
- **Integration Tests**: All API endpoints and inter-service communication MUST have integration tests
- **Contract Tests**: All public interfaces (APIs, libraries) MUST have contract tests
- **E2E Tests**: Critical user journeys MUST have end-to-end tests using ChromeDevTools
- **Performance Tests**: All AI model inference paths MUST include latency benchmarks

### Deployment Readiness

Before production deployment, features MUST pass:

1. All automated tests (unit, integration, contract, E2E)
2. Manual QA on target platforms (web, mobile)
3. Performance benchmarks (latency, throughput, resource usage)
4. Security review (OWASP Top 10 checks, dependency scanning)
5. Documentation review (API docs, user guides, runbooks)

## Governance

### Amendment Process

This constitution can be amended through the following process:

1. **Proposal**: Any team member proposes an amendment via pull request to this file
2. **Review**: Amendment is reviewed by project maintainers and stakeholders
3. **Approval**: Amendment requires majority approval from maintainers
4. **Migration**: If amendment changes existing practices, a migration plan MUST be included
5. **Documentation**: All dependent templates and documentation MUST be updated to reflect amendment

### Versioning Policy

Constitution versions follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Backward-incompatible changes (removing principles, redefining core requirements)
- **MINOR**: Backward-compatible additions (new principles, expanded guidance)
- **PATCH**: Clarifications, wording improvements, non-semantic fixes

### Exception Handling & Pragmatic Flexibility

When constitutional principles cannot be fully met due to legitimate constraints, teams MUST follow this exception process rather than being blocked:

**Exception Categories**:
1. **Technical Limitation**: Technology or platform does not support the requirement
2. **Timeline Constraint**: Critical deadline requires temporary deviation with remediation plan
3. **Resource Constraint**: Required tooling, expertise, or infrastructure unavailable
4. **Third-Party Dependency**: External system or vendor limitation prevents compliance

**Exception Process**:
1. **Document the Gap**: Clearly describe which principle(s) cannot be met and why
2. **Assess Risk**: Evaluate impact on security, reliability, maintainability, and user experience
3. **Propose Alternative**: Suggest alternative approach that mitigates risk (even if partial)
4. **Create Remediation Plan**: If exception is temporary, define steps and timeline to achieve compliance
5. **Seek Approval**: Document exception in PR description or plan.md Complexity Tracking section
6. **Review & Accept**: Maintainer reviews risk/mitigation and approves with conditions if acceptable

**Example Exception Documentation**:
```markdown
## Exception Request: Principle VI (Test-First Development)

**Principle Violated**: Test-First Development
**Category**: Timeline Constraint
**Justification**: Critical security patch required for production within 4 hours;
no time for full TDD cycle.

**Risk Assessment**:
- Security risk: HIGH if not patched immediately
- Code quality risk: MEDIUM (manual testing performed, automated tests follow)

**Alternative Approach**:
- Immediate manual testing of security fix
- Peer review by 2 security-focused maintainers
- Deploy to staging for verification before production

**Remediation Plan**:
- Write comprehensive test suite within 24 hours of deployment
- Verify tests fail without patch (red phase)
- Verify tests pass with patch (green phase)
- Schedule retrospective to prevent future emergency patches

**Approval**: @security-lead, @tech-lead
**Status**: APPROVED with 24-hour remediation commitment
```

**Non-negotiable Limits**:
- Exceptions MUST NOT compromise security (Principle XII requirements are non-waivable)
- Exceptions MUST NOT silently accumulate technical debt (remediation plan required)
- Repeated exceptions for the same principle MUST trigger constitution review
- Production deployments with active exceptions MUST be flagged and monitored

### Compliance Review

All pull requests MUST include a constitution compliance checklist:

- [ ] Feature aligns with Core Principles (I-XIII)
- [ ] Technical Standards met (platform/dependency requirements)
- [ ] Quality Gates passed (testing, deployment readiness)
- [ ] Complexity justified if constitution violations exist
- [ ] Exceptions documented with remediation plans if criteria not fully met
- [ ] Milestone achievements committed and tagged in GitHub

Project maintainers MUST verify compliance before merging.

**Version**: 1.3.0 | **Ratified**: 2025-12-04 | **Last Amended**: 2025-12-04
