# Tasks: Microservices Infrastructure & Integration Strategy

**Input**: Design documents from `/specs/002-microservices-infra/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are included based on Constitution Principle VI (Test-First Development) and observability requirements (FR-009 to FR-017).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each infrastructure capability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md Project Structure:
- **Services**: `services/{service-name}/src/`, `services/{service-name}/tests/`
- **Infrastructure**: `infrastructure/{component}/`
- **Shared**: `shared/{lib-name}/`
- **Tests**: `tests/{e2e,smoke}/`
- **Root**: `docker-compose.yml`, `.env`, `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [x] T001 Create project directory structure matching plan.md (services/, infrastructure/, shared/, tests/)
- [x] T002 Initialize Python 3.11 project with FastAPI dependencies in shared/lib-logging/
- [x] T003 [P] Create .env.example file with all environment variables from quickstart.md
- [x] T004 [P] Create .gitignore with Python, Docker, IDE, and .env patterns
- [x] T005 [P] Configure pre-commit hooks for flake8, black, and mypy in .pre-commit-config.yaml
- [x] T006 Create docker-compose.yml skeleton from quickstart.md
- [x] T007 [P] Setup Prometheus configuration in infrastructure/observability/prometheus/prometheus.yml
- [x] T008 [P] Setup Grafana datasources in infrastructure/observability/grafana/datasources/
- [x] T009 [P] Setup Loki configuration in infrastructure/observability/loki/loki-config.yaml
- [x] T010 [P] Setup Tempo configuration in infrastructure/observability/tempo/tempo.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Observability Foundation (FR-009 to FR-017)

- [x] T011 [P] Implement structured logging library in shared/lib-logging/src/logger.py (JSON format, trace_id propagation)
- [x] T012 [P] Implement distributed tracing library in shared/lib-tracing/src/tracer.py (OpenTelemetry with Tempo exporter)
- [x] T013 [P] Implement Prometheus metrics library in shared/lib-logging/src/metrics.py (Counter, Histogram, Gauge wrappers)
- [ ] T014 [P] Create observability contract validation tests in tests/e2e/test_observability_contract.py

### Database Foundation

- [ ] T015 [P] Create PostgreSQL base connection manager in shared/lib-config/src/database.py (connection pooling, health checks)
- [ ] T016 [P] Implement database migration framework setup with Alembic in shared/lib-config/migrations/

### Service Registry Foundation (Consul)

- [ ] T017 [P] Implement Consul service registration library in shared/lib-config/src/service_registry.py
- [ ] T018 [P] Create health check framework in shared/lib-config/src/health_checks.py (liveness, readiness probes)

### Configuration Management

- [ ] T019 [P] Implement environment variable loader in shared/lib-config/src/config.py (12-factor app pattern)
- [ ] T020 [P] Implement Docker secrets reader in shared/lib-config/src/secrets.py

### CI/CD Foundation

- [ ] T021 [P] Create GitHub Actions workflow template in infrastructure/ci-cd/.github/workflows/service-template.yml
- [ ] T022 [P] Create deployment scripts in infrastructure/ci-cd/scripts/deploy.ps1 (PowerShell for Windows compatibility)
- [ ] T023 [P] Create rollback script in infrastructure/ci-cd/scripts/rollback.ps1

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Unified API Access for Mobile App (Priority: P1) 🎯 MVP

**Goal**: Mobile app developers integrate with StoryMe services through a single API endpoint (Traefik Gateway) that routes requests to correct backend services

**Independent Test**: Send requests from mobile app to single gateway URL (http://localhost/), verify requests correctly route to story-service, payment-service, photo-service with consistent responses regardless of which service fulfills request

### Tests for User Story 1 (Test-First per Constitution Principle VI)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T024 [P] [US1] Contract test for Traefik routing rules in tests/integration/test_gateway_routing.py (verify /stories → story-service, /payments → payment-service)
- [x] T025 [P] [US1] Integration test for end-to-end gateway routing in tests/e2e/test_gateway_e2e.py (send request through gateway, verify backend service receives it)
- [x] T026 [P] [US1] Load test for gateway performance in tests/load/test_gateway_load.js (k6 script, verify <50ms p95 latency per Performance Goals)

### API Gateway Implementation (Traefik v3)

- [x] T027 [US1] Create Traefik configuration in services/api-gateway/traefik.yml (enable Docker provider, Consul catalog, Prometheus metrics, dashboard)
- [x] T028 [US1] Configure Traefik entrypoints in services/api-gateway/traefik.yml (HTTP :80, dashboard :8080)
- [x] T029 [US1] Implement JWT authentication middleware configuration in services/api-gateway/middlewares/auth.yml (FR-003)
- [x] T030 [US1] Implement rate limiting middleware in services/api-gateway/middlewares/rate-limit.yml (10 req/s standard, FR-007)
- [x] T031 [US1] Implement circuit breaker middleware in services/api-gateway/middlewares/circuit-breaker.yml (FR-035, prevent cascading failures)
- [x] T032 [US1] Add Traefik service to docker-compose.yml with multi-instance configuration (2 instances for HA, FR-033)
- [x] T033 [US1] Configure Traefik load balancer in docker-compose.yml (round-robin across gateway instances, FR-034)

### Sample Backend Service (Story Service) - for gateway testing

- [x] T034 [P] [US1] Create Story Service Dockerfile in services/story-service/Dockerfile (Python 3.11-slim, FastAPI)
- [x] T035 [P] [US1] Create Story Service requirements.txt in services/story-service/requirements.txt (FastAPI, SQLAlchemy, Prometheus, OpenTelemetry)
- [x] T036 [US1] Implement Story Service main application in services/story-service/src/main.py (FastAPI app with /health, /ready, /stories endpoints from contracts/story-service-openapi.yml)
- [x] T037 [US1] Implement Story Service health endpoints in services/story-service/src/health.py (liveness and readiness checks per FR-034)
- [x] T038 [US1] Integrate observability libraries in services/story-service/src/main.py (structured logging, metrics, tracing from shared libs)
- [x] T039 [US1] Configure Story Service in docker-compose.yml with Traefik labels (routing rule: PathPrefix(`/stories`))
- [x] T040 [US1] Add PostgreSQL database for Story Service in docker-compose.yml (postgres:15, story-db-data volume)

### Gateway High-Availability (FR-033 to FR-036)

- [x] T041 [US1] Implement health check monitoring in infrastructure/observability/prometheus/alerts/gateway-health.yml (alert if <2 instances healthy)
- [x] T042 [US1] Configure auto-scaling rules in infrastructure/kubernetes/gateway-hpa.yml (scale 2-10 instances based on CPU 70%, FR-036)
- [x] T043 [US1] Document manual failover procedure in infrastructure/ci-cd/runbooks/gateway-failover.md (FR-038)

### Validation

- [x] T044 [US1] Run contract tests and verify they pass (tests/integration/test_gateway_routing.py) - 9/9 PASSED
- [x] T045 [US1] Run e2e tests and verify gateway routes correctly (tests/e2e/test_gateway_e2e.py) - 8/8 PASSED
- [x] T046 [US1] Run load tests and verify <50ms p95 latency (tests/load/test_gateway_load.js) - 12.59ms EXCEEDED TARGET
- [x] T047 [US1] Verify consistent error responses from quickstart.md error handling scenarios - VERIFIED BY USER

**Checkpoint**: At this point, API Gateway is fully functional with HA, mobile apps can route all requests through single endpoint to story-service

---

## Phase 4: User Story 2 - Rapid Issue Detection and Debugging (Priority: P2)

**Goal**: Developers/operations identify production issues (slow performance, failed requests, errors) and use centralized logging/tracing to pinpoint which microservice caused problem and why

**Independent Test**: Intentionally introduce error in Story Service (slow DB query), trigger error from mobile app, verify logs/traces clearly show: which service failed, request path through services, timing of each service call, error details (30-day retention, FR-013)

### Tests for User Story 2

- [ ] T048 [P] [US2] Integration test for distributed tracing in tests/integration/test_distributed_tracing.py (verify trace_id propagation across services)
- [ ] T049 [P] [US2] Integration test for centralized logging in tests/integration/test_centralized_logging.py (verify logs from all services aggregated in Loki)
- [ ] T050 [P] [US2] Test for log search by trace_id in tests/integration/test_log_search.py (FR-015)

### Observability Stack Deployment

- [x] T051 [P] [US2] Add Prometheus service to docker-compose.yml (prom/prometheus:latest, scrape config, 90-day retention per FR-013) - DEPLOYED PHASE 1
- [x] T052 [P] [US2] Add Grafana service to docker-compose.yml (grafana/grafana:latest, datasources, dashboards) - DEPLOYED PHASE 1
- [x] T053 [P] [US2] Add Loki service to docker-compose.yml (grafana/loki:latest, 30-day retention per FR-013) - DEPLOYED PHASE 1
- [x] T054 [P] [US2] Add Tempo service to docker-compose.yml (grafana/tempo:latest, OTLP receiver, 30-day retention per FR-013) - DEPLOYED PHASE 1

### Prometheus Configuration (FR-011, FR-012)

- [x] T055 [US2] Configure Prometheus scrape targets in infrastructure/observability/prometheus/prometheus.yml (scrape all services at /metrics every 15s) - CONFIGURED PHASE 3
- [x] T056 [US2] Configure Prometheus alerting rules in infrastructure/observability/prometheus/alerts/service-health.yml (high error rate >5%, high latency >500ms p95, service down) - CONFIGURED PHASE 3
- [ ] T057 [US2] Configure Prometheus recording rules in infrastructure/observability/prometheus/rules/recording-rules.yml (pre-aggregate common queries)

### Grafana Dashboards (FR-011, FR-014)

- [x] T058 [P] [US2] Create Microservices Overview dashboard in infrastructure/observability/grafana/dashboards/microservices-overview.json (request rates, error rates, latencies per service) - COMPLETED PHASE 4
- [ ] T059 [P] [US2] Create Service Dependencies dashboard in infrastructure/observability/grafana/dashboards/service-dependencies.json (dependency health, call latency)
- [x] T060 [P] [US2] Create Logs Explorer dashboard in infrastructure/observability/grafana/dashboards/logs-explorer.json (search by trace_id, user_id, service, error type per FR-015) - COMPLETED PHASE 4
- [ ] T061 [P] [US2] Create Distributed Traces dashboard in infrastructure/observability/grafana/dashboards/traces.json (Tempo integration, trace search, flamegraphs)

### Service Instrumentation

- [x] T062 [US2] Update Story Service to emit Prometheus metrics in services/story-service/src/main.py (REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS) - COMPLETED PHASE 3
- [x] T063 [US2] Update Story Service to emit structured logs in services/story-service/src/main.py (JSON format with trace_id, user_id, duration_ms per contracts/observability-contract.md) - COMPLETED PHASE 3
- [x] T064 [US2] Update Story Service to emit distributed traces in services/story-service/src/main.py (OpenTelemetry spans with trace_id propagation) - COMPLETED PHASE 3
- [x] T065 [US2] Expose /metrics endpoint in Story Service at port 9090 for Prometheus scraping - COMPLETED PHASE 3

### Alerting Configuration (FR-012)

- [x] T066 [US2] Configure Alertmanager in infrastructure/observability/alertmanager/alertmanager.yml (route alerts to Slack/PagerDuty/email) - COMPLETED PHASE 4
- [ ] T067 [US2] Test high error rate alert (trigger >5% errors, verify alert fires within 2 minutes)
- [ ] T068 [US2] Test high latency alert (trigger >500ms p95, verify alert fires within 5 minutes)

### Validation

- [ ] T069 [US2] Run distributed tracing test and verify trace_id propagates correctly (tests/integration/test_distributed_tracing.py)
- [ ] T070 [US2] Run centralized logging test and verify logs aggregated (tests/integration/test_centralized_logging.py)
- [ ] T071 [US2] Simulate production issue (slow query), search logs by trace_id, verify root cause identifiable within 2 minutes
- [ ] T072 [US2] Verify 30-day log/trace retention configured and working

**Checkpoint**: At this point, full observability stack operational, developers can identify root cause of 90% of production issues using logs/traces (SC-005)

---

## Phase 5: User Story 3 - Automated Service Deployment (Priority: P3)

**Goal**: Developer commits code to microservice, CI/CD pipeline automatically runs tests, builds service, deploys to production with zero-downtime, no manual intervention, automated rollback on failure

**Independent Test**: Commit code change to Story Service, verify pipeline automatically runs unit tests, integration tests, builds Docker image, deploys to production with zero-downtime, other services unaffected (FR-019), rollback works if tests fail (FR-020)

### Tests for User Story 3

- [x] T073 [P] [US3] Integration test for CI/CD pipeline in tests/integration/test_ci_pipeline.py (trigger pipeline, verify stages execute in order)
- [x] T074 [P] [US3] Test for zero-downtime deployment in tests/integration/test_zero_downtime_deploy.py (deploy new version, verify no request failures)
- [x] T075 [P] [US3] Test for automated rollback in tests/integration/test_auto_rollback.py (deploy bad version, verify rollback triggered)

### GitHub Actions CI/CD Pipeline (FR-016 to FR-023)

- [x] T076 [US3] Create Story Service CI workflow in .github/workflows/story-service-ci.yml (triggers on commits to services/story-service/**)
- [x] T077 [US3] Implement lint stage in .github/workflows/story-service-ci.yml (flake8, black, mypy on Windows runner)
- [x] T078 [US3] Implement unit test stage in .github/workflows/story-service-ci.yml (pytest with coverage, fail if coverage <80%)
- [x] T079 [US3] Implement integration test stage in .github/workflows/story-service-ci.yml (pytest + Testcontainers, FR-017)
- [x] T080 [US3] Implement security scan stage in .github/workflows/story-service-ci.yml (safety check, Trivy container scan, FR-017)
- [x] T081 [US3] Implement contract compatibility check stage in .github/workflows/story-service-ci.yml (validate API contract against dependencies, FR-021)
- [x] T082 [US3] Implement Docker build stage in .github/workflows/story-service-ci.yml (build image tagged with commit SHA and version)
- [x] T083 [US3] Implement deployment stage in .github/workflows/story-service-ci.yml (deploy to staging with blue-green strategy, FR-019)

### Deployment Automation

- [x] T084 [US3] Create blue-green deployment script in infrastructure/ci-cd/scripts/deploy-blue-green.ps1 (launch green instances, health check, switch traffic, keep blue for rollback)
- [x] T085 [US3] Create rolling deployment script in infrastructure/ci-cd/scripts/deploy-rolling.ps1 (update instances one at a time, health check between updates)
- [x] T086 [US3] Implement health monitoring during deployment in infrastructure/ci-cd/scripts/monitor-deployment.ps1 (check error rate <5%, latency <500ms p95 for 10 minutes post-deploy)
- [x] T087 [US3] Implement automated rollback script in infrastructure/ci-cd/scripts/auto-rollback.ps1 (rollback to previous version if health checks fail, FR-020)

### Deployment History Tracking

- [x] T088 [US3] Create deployment history logger in infrastructure/ci-cd/scripts/log-deployment.ps1 (record service, version, commit SHA, timestamp, status to deployment-history.json, FR-022)
- [x] T089 [US3] Implement deployment dashboard in infrastructure/observability/grafana/dashboards/deployments.json (show deployment history, success rate, rollback frequency)

### Kubernetes Deployment Configuration (Production)

- [x] T090 [P] [US3] Create Story Service Deployment manifest in infrastructure/kubernetes/story-service-deployment.yml (3 replicas, liveness/readiness probes, resource limits)
- [x] T091 [P] [US3] Create Story Service Service manifest in infrastructure/kubernetes/story-service-service.yml (ClusterIP, port 8000)
- [x] T092 [P] [US3] Create Story Service HorizontalPodAutoscaler in infrastructure/kubernetes/story-service-hpa.yml (scale 2-10 replicas, CPU 70% target)

### Validation

- [ ] T093 [US3] Run CI pipeline test and verify all stages execute (tests/integration/test_ci_pipeline.py)
- [ ] T094 [US3] Commit test change to Story Service, verify automated deployment to staging completes successfully
- [ ] T095 [US3] Verify zero-downtime deployment (tests/integration/test_zero_downtime_deploy.py, should show 100% request success during deployment)
- [ ] T096 [US3] Trigger failed deployment, verify automated rollback completes within 2 minutes (tests/integration/test_auto_rollback.py)

**Checkpoint**: At this point, automated CI/CD pipeline operational, developers can deploy services with zero manual intervention, 95% deployment success rate (SC-010)

---

## Phase 6: User Story 4 - Service Version Compatibility Management (Priority: P3)

**Goal**: Developer deploys new version of microservice (Story Service v1→v2) and system ensures: older mobile apps can still communicate, other microservices calling this service continue to work, deployment happens without downtime

**Independent Test**: Deploy Story Service v2 with breaking API change, verify: mobile apps using v1 endpoints still work, gateway routes v1 requests to v1 compatibility layer or v1 instances, v2 clients get new API, transition happens without service interruption (FR-008, FR-026)

### Tests for User Story 4

- [x] T097 [P] [US4] Contract test for API versioning in tests/contract/test_api_versioning.py (verify /v1/stories and /v2/stories both work)
- [x] T098 [P] [US4] Integration test for multi-version deployment in tests/integration/test_multi_version_deploy.py (deploy v2, verify v1 still accessible)
- [x] T099 [P] [US4] Integration test for contract validation in tests/integration/test_contract_validation.py (verify breaking changes detected before deployment)

### API Versioning Infrastructure

- [x] T100 [US4] Implement semantic versioning enforcement in infrastructure/ci-cd/scripts/validate-semver.ps1 (parse version from git tags, validate MAJOR.MINOR.PATCH format, FR-024)
- [x] T101 [US4] Implement breaking change detection in infrastructure/ci-cd/scripts/detect-breaking-changes.ps1 (compare OpenAPI schemas, flag breaking changes, require MAJOR version bump, FR-025)
- [x] T102 [US4] Create API contract registry in infrastructure/ci-cd/contracts-registry/ (store OpenAPI schemas per service/version, FR-027)

### Multi-Version Service Support

- [ ] T103 [US4] Update Story Service to support /v1/ and /v2/ endpoints in services/story-service/src/main.py (versioned routers)
- [ ] T104 [US4] Implement v1 compatibility layer in services/story-service/src/api/v1/ (maintain old API contract while v2 uses new contract)
- [ ] T105 [US4] Update Traefik routing to support versioned paths in services/api-gateway/traefik.yml (route /v1/stories to v1 endpoints, /v2/stories to v2 endpoints)

### Service Contract Validation (FR-030 - Level 1 & Level 2)

- [ ] T106 [US4] Create manual integration testing checklist in infrastructure/ci-cd/checklists/integration-checklist.md (Level 1 approach per research.md, for beginner teams)
- [ ] T107 [US4] Implement automated integration test suite in tests/integration/test_service_contracts.py (Level 2 approach, verify Story Service can call Payment Service, Photo Service with expected contracts)
- [ ] T108 [US4] Configure integration tests to run in CI pipeline in .github/workflows/story-service-ci.yml (block deployment if integration tests fail, FR-030 Level 2)

### Gradual Rollout (FR-032)

- [ ] T109 [US4] Implement canary deployment script in infrastructure/ci-cd/scripts/deploy-canary.ps1 (deploy v2 to 10% traffic, monitor metrics, increase to 50%, then 100%)
- [ ] T110 [US4] Implement traffic splitting configuration in services/api-gateway/middlewares/traffic-split.yml (Traefik weighted routing, 90% v1 / 10% v2 initially)

### Service Registry with Versioning

- [ ] T111 [US4] Update Consul registration to include version tags in shared/lib-config/src/service_registry.py (register as story-service:v1.0.0, story-service:v2.0.0)
- [ ] T112 [US4] Implement version-aware service discovery in shared/lib-config/src/service_discovery.py (lookup services by name and version range, e.g., "story-service >=v1.0.0 <v2.0.0")

### Validation

- [ ] T113 [US4] Deploy Story Service v2.0.0 with breaking change, verify v1 endpoints still accessible (tests/contract/test_api_versioning.py)
- [ ] T114 [US4] Run multi-version deployment test (tests/integration/test_multi_version_deploy.py, should show both v1 and v2 working simultaneously)
- [ ] T115 [US4] Verify breaking change detection prevents deployment without version bump (tests/integration/test_contract_validation.py)
- [ ] T116 [US4] Test gradual rollout (deploy v2 with 10% traffic, verify metrics, increase to 100%, no errors)

**Checkpoint**: At this point, version compatibility system operational, services can evolve independently with backward compatibility (SC-013: zero outages from version incompatibilities)

---

## Phase 7: Additional Services Deployment

**Purpose**: Deploy remaining microservices using established patterns from User Stories 1-4

### Payment Service

- [ ] T117 [P] Create Payment Service structure matching Story Service pattern in services/payment-service/
- [ ] T118 [P] Implement Payment Service with observability in services/payment-service/src/main.py (endpoints: /subscriptions/check, /subscriptions/purchase from contracts/api-gateway-routes.yml)
- [ ] T119 [P] Add Payment Service to docker-compose.yml with Traefik routing (PathPrefix(`/payments`))
- [ ] T120 [P] Create Payment Service CI workflow in .github/workflows/payment-service-ci.yml
- [ ] T121 Test Payment Service independently and integrate with Story Service

### Photo Processing Service

- [ ] T122 [P] Create Photo Service structure in services/photo-service/
- [ ] T123 [P] Implement Photo Service with observability in services/photo-service/src/main.py (endpoints: /photos/upload, /photos/{id}/status)
- [ ] T124 [P] Add Photo Service to docker-compose.yml with Traefik routing (PathPrefix(`/photos`), rate-limit-strict middleware)
- [ ] T125 [P] Create Photo Service CI workflow in .github/workflows/photo-service-ci.yml
- [ ] T126 Test Photo Service independently

### User Service

- [ ] T127 [P] Create User Service structure in services/user-service/
- [ ] T128 [P] Implement User Service with observability in services/user-service/src/main.py (endpoints: /users/register, /users/login, /users/{id})
- [ ] T129 [P] Add User Service to docker-compose.yml with Traefik routing
- [ ] T130 [P] Create User Service CI workflow in .github/workflows/user-service-ci.yml
- [ ] T131 Test User Service independently

### Content Service

- [ ] T132 [P] Create Content Service structure in services/content-service/
- [ ] T133 [P] Implement Content Service with observability in services/content-service/src/main.py
- [ ] T134 [P] Add Content Service to docker-compose.yml with Traefik routing
- [ ] T135 [P] Create Content Service CI workflow in .github/workflows/content-service-ci.yml
- [ ] T136 Test Content Service independently

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple services and production readiness

### Documentation

- [ ] T137 [P] Create architecture diagram in docs/architecture.md (showing all services, gateway, observability stack, data flow)
- [ ] T138 [P] Create deployment guide in docs/deployment-guide.md (production deployment steps, checklist from quickstart.md)
- [ ] T139 [P] Create troubleshooting guide in docs/troubleshooting.md (common issues, resolution steps from quickstart.md)
- [ ] T140 [P] Create API documentation portal in docs/api/ (aggregate OpenAPI specs from all services)

### Security Hardening

- [ ] T141 [P] Implement API Gateway TLS/HTTPS in services/api-gateway/traefik.yml (Let's Encrypt automatic certificates)
- [ ] T142 [P] Implement secret rotation for JWT_SECRET in infrastructure/ci-cd/scripts/rotate-secrets.ps1
- [ ] T143 [P] Add security headers middleware in services/api-gateway/middlewares/security-headers.yml (HSTS, CSP, X-Frame-Options)
- [ ] T144 [P] Run OWASP security scan in .github/workflows/security-scan.yml (ZAP or similar tool)

### Performance Optimization

- [ ] T145 [P] Optimize database queries in all services (add indexes, query optimization per observability metrics)
- [ ] T146 [P] Implement response caching in services/api-gateway/middlewares/cache.yml (cache GET requests for 60s)
- [ ] T147 [P] Configure connection pooling in shared/lib-config/src/database.py (PostgreSQL pool size: 10-50)

### Disaster Recovery (FR-038, FR-039)

- [ ] T148 Create disaster recovery runbook in infrastructure/ci-cd/runbooks/disaster-recovery.md (backup procedures, restore procedures, failover steps)
- [ ] T149 Implement database backup automation in infrastructure/ci-cd/scripts/backup-databases.ps1 (daily backups to cloud storage)
- [ ] T150 Schedule quarterly disaster recovery drill and document results

### Production Checklist

- [ ] T151 Validate quickstart.md against actual deployment (ensure all steps work on fresh Windows machine)
- [ ] T152 Run full e2e test suite in tests/e2e/ (simulate production traffic, verify all user stories work together)
- [ ] T153 Run load tests against full stack (k6 scripts, target 1000+ concurrent requests, verify performance goals)
- [ ] T154 Verify all success criteria from spec.md (SC-001 to SC-020)
- [ ] T155 Tag production-ready milestone: git tag v1.0.0 (Constitution Principle XIII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Independent after Foundational
  - User Story 2 (P2): Independent after Foundational (enhances US1 but not blocking)
  - User Story 3 (P3): Independent after Foundational (builds on US1 pattern)
  - User Story 4 (P3): Depends on US1 (needs running service for versioning)
- **Additional Services (Phase 7)**: Depends on US1-US4 patterns established
- **Polish (Phase 8)**: Depends on all desired functionality complete

### User Story Dependencies

- **User Story 1 (API Gateway)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (Observability)**: Can start after Foundational - Integrates with US1 but independently testable
- **User Story 3 (CI/CD)**: Can start after Foundational - Uses patterns from US1 but independently testable
- **User Story 4 (Versioning)**: Soft dependency on US1 (needs running service to demonstrate versioning)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution Principle VI)
- Foundation libraries before service implementation
- Services before gateway routing
- Core implementation before validation
- Story validation complete before moving to next priority

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T003, T004, T005 (config files) can run in parallel
- T007, T008, T009, T010 (observability configs) can run in parallel

**Foundational Phase (Phase 2)**:
- T011, T012, T013 (observability libraries) can run in parallel
- T015, T016 (database foundation) can run in parallel
- T017, T018 (service registry) can run in parallel
- T019, T020 (configuration) can run in parallel
- T021, T022, T023 (CI/CD scripts) can run in parallel

**User Story 1**:
- T024, T025, T026 (tests) can run in parallel
- T034, T035 (Dockerfile, requirements) can run in parallel
- T029, T030, T031 (middlewares) can run in parallel

**User Story 2**:
- T048, T049, T050 (tests) can run in parallel
- T051, T052, T053, T054 (observability stack) can run in parallel
- T058, T059, T060, T061 (dashboards) can run in parallel

**User Story 3**:
- T073, T074, T075 (tests) can run in parallel
- T090, T091, T092 (Kubernetes manifests) can run in parallel

**User Story 4**:
- T097, T098, T099 (tests) can run in parallel

**Additional Services (Phase 7)**:
- All services (Payment, Photo, User, Content) can be developed in parallel once patterns established

**Polish Phase (Phase 8)**:
- T137, T138, T139, T140 (documentation) can run in parallel
- T141, T142, T143, T144 (security) can run in parallel
- T145, T146, T147 (performance) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T024: "Contract test for Traefik routing rules"
Task T025: "Integration test for end-to-end gateway routing"
Task T026: "Load test for gateway performance"

# Launch all middleware configs together:
Task T029: "JWT authentication middleware"
Task T030: "Rate limiting middleware"
Task T031: "Circuit breaker middleware"

# Launch service foundation in parallel:
Task T034: "Story Service Dockerfile"
Task T035: "Story Service requirements.txt"
```

---

## Parallel Example: Additional Services (Phase 7)

```bash
# After US1-US4 patterns established, all services can be built in parallel:
Developer A: Tasks T117-T121 (Payment Service)
Developer B: Tasks T122-T126 (Photo Service)
Developer C: Tasks T127-T131 (User Service)
Developer D: Tasks T132-T136 (Content Service)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T010)
2. Complete Phase 2: Foundational (T011-T023) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T024-T047)
4. **STOP and VALIDATE**: Test API Gateway independently
   - Send requests through http://localhost/
   - Verify routing to story-service works
   - Verify HA (2 gateway instances)
   - Run load tests (<50ms p95 latency)
5. Deploy/demo if ready

**Milestone**: Tag v0.1.0 "API Gateway operational with HA"

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + Foundational → Infrastructure ready
   - **Milestone**: Tag v0.0.1 "Foundation complete"

2. **MVP** (Phase 3): User Story 1 → API Gateway works
   - Test independently → Deploy/Demo
   - **Milestone**: Tag v0.1.0 "API Gateway operational" 🎯

3. **Observability** (Phase 4): User Story 2 → Full observability stack
   - Test independently → Deploy/Demo
   - **Milestone**: Tag v0.2.0 "Observability integrated"

4. **CI/CD** (Phase 5): User Story 3 → Automated deployments
   - Test independently → Deploy/Demo
   - **Milestone**: Tag v0.3.0 "CI/CD automated"

5. **Versioning** (Phase 6): User Story 4 → Version compatibility
   - Test independently → Deploy/Demo
   - **Milestone**: Tag v0.4.0 "Multi-version support"

6. **Full Services** (Phase 7): All microservices deployed
   - **Milestone**: Tag v0.9.0 "All services operational"

7. **Production Ready** (Phase 8): Polish + validation
   - **Milestone**: Tag v1.0.0 "Production-ready with HA" 🚀

### Parallel Team Strategy

With multiple developers:

1. **Weeks 1-2**: Team completes Setup + Foundational together (T001-T023)
2. **Week 3**: Once Foundational done:
   - Developer A: User Story 1 - API Gateway (T024-T047)
   - Developer B: User Story 2 - Observability (T048-T072)
   - Developer C: User Story 3 - CI/CD (T073-T096)
3. **Week 4**:
   - Developer A: User Story 4 - Versioning (T097-T116)
   - Developer B: Payment Service (T117-T121)
   - Developer C: Photo Service (T122-T126)
4. **Week 5**:
   - Developer A: User Service (T127-T131)
   - Developer B: Content Service (T132-T136)
   - Developer C: Polish (T137-T155)
5. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 155

**Tasks by Phase**:
- Phase 1 (Setup): 10 tasks
- Phase 2 (Foundational): 13 tasks (BLOCKING)
- Phase 3 (User Story 1 - API Gateway): 24 tasks
- Phase 4 (User Story 2 - Observability): 25 tasks
- Phase 5 (User Story 3 - CI/CD): 24 tasks
- Phase 6 (User Story 4 - Versioning): 20 tasks
- Phase 7 (Additional Services): 20 tasks
- Phase 8 (Polish): 19 tasks

**Tasks by User Story**:
- User Story 1 (API Gateway): 24 tasks
- User Story 2 (Observability): 25 tasks
- User Story 3 (CI/CD): 24 tasks
- User Story 4 (Versioning): 20 tasks

**Parallel Opportunities**: 67 tasks marked [P] can run in parallel

**Independent Test Criteria**:
- US1: Gateway routes requests correctly, <50ms p95 latency, HA with 2+ instances
- US2: Logs/traces show error root cause, 30-day retention, alerts fire correctly
- US3: Automated deployment works, zero-downtime verified, rollback works
- US4: V1 and v2 APIs work simultaneously, breaking changes detected

**Suggested MVP Scope**: User Story 1 only (API Gateway) = 47 total tasks (Setup + Foundational + US1)

**Format Validation**: ✅ All 155 tasks follow checklist format with checkboxes, IDs, [P] markers where applicable, [Story] labels for user story phases, and file paths

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story (US1, US2, US3, US4) for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Constitution Principle VI)
- Commit after each task or logical group (Constitution Principle XIII)
- Stop at any checkpoint to validate story independently
- Windows compatibility maintained throughout (PowerShell scripts, Docker Desktop)
- All paths are absolute or relative to repository root
- Observability built into every service from the start
- Follow research.md technology decisions throughout implementation
