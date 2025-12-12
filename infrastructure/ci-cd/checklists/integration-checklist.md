# Integration Testing Checklist

**Purpose**: Manual verification of service-to-service contracts and API Gateway integration
**Level**: Level 1 (Manual Testing) - Per FR-030 staged progression approach
**Audience**: Developers and QA engineers deploying new service versions
**When to Use**: Before deploying any service version that changes API contracts or adds new endpoints

---

## Story Service v2.0 Deployment Checklist

### API Version Compatibility

**V1 API Endpoints (Backward Compatibility)**
- [ ] Story Service v1 endpoint accessible: `GET http://localhost/v1/stories`
- [ ] V1 returns expected format: `{stories: [...], total: N}`
- [ ] V1 story object uses 'content' field (not 'body')
- [ ] V1 list endpoint supports pagination: `?limit=10&offset=0`
- [ ] V1 story detail accessible: `GET http://localhost/v1/stories/{id}`
- [ ] V1 personalize endpoint works: `POST http://localhost/v1/stories/{id}/personalize`

**V2 API Endpoints (New Features)**
- [ ] Story Service v2 endpoint accessible: `GET http://localhost/v2/stories`
- [ ] V2 returns new format: `{data: [...], pagination: {...}}`
- [ ] V2 story object uses 'body' field (not 'content')
- [ ] V2 includes pagination metadata: `{total, limit, offset, has_more}`
- [ ] V2 story object includes 'metadata' field
- [ ] V2 story detail accessible: `GET http://localhost/v2/stories/{id}`
- [ ] V2 search endpoint works: `GET http://localhost/v2/stories/search?query=dragon`
- [ ] V2 personalize endpoint works: `POST http://localhost/v2/stories/{id}/personalize`

---

## Payment Service Integration

**Story Service → Payment Service Communication**
- [ ] Story Service can call Payment Service `/subscriptions/check` endpoint
- [ ] Payment Service returns expected JSON structure: `{"user_id": "...", "tier": "free|subscriber"}`
- [ ] Story Service handles payment service timeout gracefully (fallback to free tier)
- [ ] Story Service handles payment service 500 errors with retry logic
- [ ] Story Service respects tier limits (free: 5 stories, subscriber: unlimited)
- [ ] Story Service logs payment service calls with trace_id for debugging

**Error Scenarios**
- [ ] Payment Service down: Story Service defaults to free tier access
- [ ] Payment Service returns invalid JSON: Story Service logs error and defaults to free tier
- [ ] Payment Service responds slow (>3s): Story Service times out and continues

---

## Photo Service Integration

**Story Service → Photo Service Communication**
- [ ] Story Service can upload photos to Photo Service `/process` endpoint
- [ ] Photo Service accepts multipart/form-data with JPEG/PNG files
- [ ] Photo Service returns face_swap_id for tracking processing status
- [ ] Story Service can poll `/status/{face_swap_id}` for completion
- [ ] Story Service handles photo upload failures gracefully
- [ ] Story Service logs photo processing requests with trace_id

**Error Scenarios**
- [ ] Photo Service down: Story Service returns error to user with retry message
- [ ] Photo upload too large (>5MB): Story Service validates before upload
- [ ] Invalid file format: Story Service validates MIME type before upload
- [ ] Photo processing fails: Story Service displays user-friendly error

---

## API Gateway Routing

**Versioned Routing**
- [ ] Gateway routes `/v1/stories` to Story Service v1 endpoints
- [ ] Gateway routes `/v2/stories` to Story Service v2 endpoints
- [ ] Gateway applies standard middleware chain (CORS, rate limit, tracing)
- [ ] Gateway forwards trace_id headers correctly
- [ ] Gateway load balances across 2+ Story Service instances (if multiple running)

**High Availability**
- [ ] Gateway returns 503 if all Story Service instances unhealthy
- [ ] Gateway performs health checks every 10s on `/health` endpoint
- [ ] Gateway removes unhealthy instances from rotation automatically
- [ ] Gateway adds recovered instances back to rotation after health check passes

**Rate Limiting**
- [ ] Gateway enforces 10 req/s average rate limit
- [ ] Gateway allows burst up to 20 requests
- [ ] Gateway returns 429 Too Many Requests when limit exceeded
- [ ] Rate limit headers included in response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

---

## Zero-Downtime Deployment

**Before Deployment**
- [ ] New version (v2.0.0) built and tagged in Docker registry
- [ ] Health check endpoint `/health` returns 200 OK in new version
- [ ] Database migrations applied successfully (if any)
- [ ] Environment variables configured correctly
- [ ] Secrets (API keys, DB passwords) loaded from secure store

**During Deployment**
- [ ] Old version (v1.0.0) continues serving traffic during rollout
- [ ] New version deployed with RollingUpdate strategy (maxUnavailable: 0)
- [ ] Health checks pass for new version before receiving traffic
- [ ] Both v1 and v2 endpoints accessible during transition period
- [ ] No 5xx errors observed in gateway logs during deployment

**After Deployment**
- [ ] New version serving traffic successfully
- [ ] Old version instances terminated gracefully (no active connections dropped)
- [ ] Metrics show normal latency (p95 <50ms gateway, <100ms service-to-service)
- [ ] No error rate spike in last 10 minutes
- [ ] Logs show both v1 and v2 requests being served

---

## Observability Validation

**Metrics**
- [ ] Prometheus scraping metrics from Story Service `/metrics` endpoint
- [ ] Grafana dashboard shows Story Service health (CPU, memory, request rate)
- [ ] Request duration histogram shows p95 latency <100ms
- [ ] Error rate <1% in last 10 minutes
- [ ] Service discovery shows Story Service registered in Consul

**Logging**
- [ ] Story Service logs appear in Loki (query: `{service="story-service"}`)
- [ ] Logs include trace_id for request correlation
- [ ] Logs in JSON format with structured fields (service, level, message, timestamp)
- [ ] Error logs include stack traces and context
- [ ] Log level set correctly (INFO for production, DEBUG for development)

**Tracing**
- [ ] Distributed traces appear in Tempo
- [ ] Trace spans show full request path: Gateway → Story Service → (Payment/Photo Service)
- [ ] Trace IDs propagated correctly across service boundaries
- [ ] Span durations reasonable (no blocking operations >1s)
- [ ] Error spans tagged with error=true and error message

**Alerting**
- [ ] Alert rules configured for Story Service in Prometheus
- [ ] Test alert fires correctly (set health check to fail temporarily)
- [ ] Alertmanager routes alerts to correct channels (Slack/email)
- [ ] Alert includes runbook link for troubleshooting
- [ ] Alert auto-resolves when issue fixed

---

## Rollback Plan

**Trigger Conditions**
- [ ] Error rate >5% for 5 consecutive minutes
- [ ] P95 latency >500ms for 5 consecutive minutes
- [ ] Health checks failing on >50% of instances
- [ ] Critical bug discovered affecting user data integrity

**Rollback Steps**
1. [ ] Stop deployment of new version
2. [ ] Scale up old version instances (if terminated)
3. [ ] Update gateway routing to send 100% traffic to old version
4. [ ] Verify old version serving traffic successfully
5. [ ] Investigate root cause in new version
6. [ ] Document incident and lessons learned

**Rollback Verification**
- [ ] Service restored to normal operation within 5 minutes
- [ ] Error rate returns to <1%
- [ ] Latency returns to normal (p95 <100ms)
- [ ] No data loss or corruption during rollback
- [ ] Post-incident report created

---

## Breaking Change Validation

**Semantic Versioning**
- [ ] Version incremented correctly for changes:
  - MAJOR: Breaking changes (v1.0.0 → v2.0.0)
  - MINOR: New features backward compatible (v1.0.0 → v1.1.0)
  - PATCH: Bug fixes backward compatible (v1.0.0 → v1.0.1)

**Contract Registry**
- [ ] OpenAPI schema stored in `infrastructure/ci-cd/contracts-registry/story-service/v2.0.0/openapi.json`
- [ ] Breaking changes documented in changelog
- [ ] Breaking change detection script executed: `detect-breaking-changes.ps1`
- [ ] Script output reviewed and approved by team lead

**Client Compatibility**
- [ ] V1 mobile apps continue working (no breaking changes to v1 endpoints)
- [ ] V2 mobile apps tested against new v2 endpoints
- [ ] Web app supports both v1 and v2 API versions
- [ ] Documentation updated with v2 API changes

---

## Security Checklist

**Authentication & Authorization**
- [ ] Gateway validates API keys/JWT tokens before forwarding requests
- [ ] Story Service validates authorization for personalized content
- [ ] Service-to-service communication uses mutual TLS (production only)
- [ ] Secrets not logged or exposed in error messages

**Input Validation**
- [ ] Story Service validates all user inputs (XSS prevention)
- [ ] File uploads validated (size, MIME type, content scanning)
- [ ] SQL injection prevention (parameterized queries or ORM)
- [ ] Rate limiting prevents abuse and DDoS

**Data Protection**
- [ ] PII (user data) encrypted at rest and in transit
- [ ] Database credentials rotated regularly
- [ ] Access logs comply with privacy regulations (GDPR, CCPA)
- [ ] Sensitive data redacted from logs and traces

---

## Performance Validation

**Load Testing Results**
- [ ] Baseline load test executed (100 req/s for 5 minutes)
- [ ] P95 latency <50ms at gateway
- [ ] P95 latency <100ms service-to-service
- [ ] Error rate <0.1% under normal load
- [ ] System handles 2x normal load (200 req/s) without degradation

**Resource Utilization**
- [ ] CPU usage <70% under normal load
- [ ] Memory usage stable (no memory leaks over 1 hour test)
- [ ] Database connection pool not exhausted
- [ ] Disk I/O within acceptable limits
- [ ] Network bandwidth sufficient for traffic volume

---

## Sign-Off

**Completed By**: ___________________________
**Date**: ___________________________
**Version Deployed**: ___________________________
**Approver**: ___________________________
**Date Approved**: ___________________________

**Notes**:
- Any checklist items marked "not applicable" must be documented with justification
- Failed items must be resolved or have mitigation plan before deployment
- This checklist serves as pre-deployment validation for Level 1 teams
- Migrate to automated integration tests (Level 2) after 3-6 months

---

**Next Steps After Completion**:
1. ✅ All items checked → Proceed with deployment
2. ⚠️ Any items failed → Review with team, fix issues, re-test
3. 📊 Record checklist completion time to identify automation opportunities
4. 🎯 After 10+ deployments, evaluate migration to Level 2 automated tests

**Related Documentation**:
- [Deployment Runbook](../runbooks/story-service-deployment.md)
- [Rollback Procedure](../runbooks/rollback-procedure.md)
- [Integration Test Automation Guide](../../tests/integration/README.md)
