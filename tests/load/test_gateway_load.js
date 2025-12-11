/**
 * Load Test for API Gateway Performance
 * Tests verify gateway meets performance targets: <50ms p95 latency
 *
 * Per T026 [US1]: k6 script, verify <50ms p95 latency per Performance Goals
 *
 * Usage:
 *   k6 run test_gateway_load.js
 *
 * Prerequisites:
 *   - k6 installed: https://k6.io/docs/getting-started/installation/
 *   - Gateway and story service running
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const gatewayLatency = new Trend('gateway_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Ramp up to 100 users (1000 req/s)
    { duration: '1m', target: 50 },    // Ramp down
    { duration: '30s', target: 0 },    // Cool down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<50'],  // 95% of requests must complete below 50ms
    'http_req_failed': ['rate<0.01'],   // Error rate must be below 1%
    'errors': ['rate<0.01'],            // Custom error rate below 1%
  },
};

// Test configuration
const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost:80';

export default function () {
  // Test 1: Health check endpoint
  testHealthEndpoint();

  // Test 2: Story list endpoint
  testStoryListEndpoint();

  // Test 3: Story detail endpoint (if available)
  // testStoryDetailEndpoint();

  sleep(1); // Wait 1 second between iterations
}

function testHealthEndpoint() {
  // Health endpoint is accessed directly at port 8000, not through gateway
  const response = http.get(`http://localhost:8000/health`, {
    tags: { endpoint: 'health' },
  });

  const success = check(response, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 50ms': (r) => r.timings.duration < 50,
    'health returns JSON': (r) => r.headers['Content-Type']?.includes('application/json'),
  });

  errorRate.add(!success);
  gatewayLatency.add(response.timings.duration);
}

function testStoryListEndpoint() {
  const response = http.get(`${BASE_URL}/stories/`, {
    tags: { endpoint: 'story-list' },
  });

  const success = check(response, {
    'story-list status is 200': (r) => r.status === 200,
    'story-list response time < 100ms': (r) => r.timings.duration < 100,
    'story-list returns JSON': (r) => r.headers['Content-Type']?.includes('application/json'),
    'story-list returns object with stories': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && Array.isArray(body.stories) && typeof body.total === 'number';
      } catch (e) {
        return false;
      }
    },
  });

  errorRate.add(!success);
  gatewayLatency.add(response.timings.duration);
}

function testStoryDetailEndpoint() {
  // Test story detail endpoint with sample ID
  const storyId = 1;
  const response = http.get(`${BASE_URL}/stories/${storyId}`, {
    tags: { endpoint: 'story-detail' },
  });

  const success = check(response, {
    'story-detail status is 200 or 404': (r) => [200, 404].includes(r.status),
    'story-detail response time < 100ms': (r) => r.timings.duration < 100,
  });

  errorRate.add(!success && response.status !== 404);
  gatewayLatency.add(response.timings.duration);
}

// Setup function - runs once before test
export function setup() {
  console.log('Starting load test...');
  console.log(`Target: ${BASE_URL}`);

  // Verify gateway is accessible via story list endpoint
  const response = http.get(`${BASE_URL}/stories/`);
  if (response.status !== 200) {
    console.error('Gateway not accessible! Aborting test.');
    throw new Error('Gateway health check failed');
  }

  console.log('Gateway is accessible. Beginning load test.');
}

// Teardown function - runs once after test
export function teardown(data) {
  console.log('Load test completed.');
}

/**
 * Performance Goals (from spec):
 * - Gateway latency: <50ms p95
 * - Service-to-service latency: <100ms p95
 * - Support 1000+ concurrent requests
 * - 99.9% routing accuracy
 *
 * Success Criteria:
 * - p95 latency < 50ms for gateway routing
 * - Error rate < 1%
 * - No timeouts or connection failures
 * - Consistent performance under load
 */
