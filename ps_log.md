=== Step 1: Pre-Deployment Checks ===
Checking Docker...
[OK] Docker installed: Docker version 27.3.1, build ce12230
Checking Docker daemon...
[OK] Docker daemon is running
Checking port availability...
[OK] All required ports are available
Checking disk space...
[OK] Disk space: 74.64 GB free

=== Step 2: Environment Setup ===
[OK] .env file already exists

=== Step 3: Deploying Services ===
Stopping existing services...
[OK] Stopped existing services
Pulling Docker images...
[+] Pulling 14/14
 ✔ traefik-2 Skipped - Image is already being pulled by traefik-1                                                  0.0s
 ✔ story-service Skipped - No image to be pulled                                                                   0.0s
 ✔ grafana Pulled                                                                                                  3.1s
 ✔ tempo Pulled                                                                                                   10.6s
   ✔ 66525c745205 Download complete                                                                                5.3s
   ✔ 15151ea6b1f6 Download complete                                                                                1.4s
   ✔ 8660ce41f326 Download complete                                                                                1.4s
   ✔ bfa7b2a6bda6 Download complete                                                                                1.4s
   ✔ 731fd7cec8b4 Download complete                                                                                1.0s
 ✔ prometheus Pulled                                                                                               2.9s
 ✔ loki Pulled                                                                                                     3.1s
 ✔ traefik-1 Pulled                                                                                                2.9s
 ✔ consul Pulled                                                                                                   2.9s
 ✔ story-db Pulled                                                                                                 3.0s
Building Story Service image...
[+] Building 2.5s (19/19) FINISHED                                                                 docker:desktop-linux
 => [story-service internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 1.56kB                                                                             0.0s
 => WARN: FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 6)                                     0.0s
 => [story-service internal] load metadata for docker.io/library/python:3.11-slim                                  1.9s
 => [story-service internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                                    0.0s
 => [story-service internal] load build context                                                                    0.0s
 => => transferring context: 1.70kB                                                                                0.0s
 => [story-service builder 1/5] FROM docker.io/library/python:3.11-slim@sha256:193fdd0bbcb3d2ae612bd6cc3548d2f7c7  0.1s
 => => resolve docker.io/library/python:3.11-slim@sha256:193fdd0bbcb3d2ae612bd6cc3548d2f7c78d65b549fcaa8af75624c4  0.0s
 => CACHED [story-service stage-1 2/9] WORKDIR /app                                                                0.0s
 => CACHED [story-service stage-1 3/9] RUN apt-get update &&     apt-get install -y --no-install-recommends     c  0.0s
 => CACHED [story-service builder 2/5] WORKDIR /build                                                              0.0s
 => CACHED [story-service builder 3/5] RUN apt-get update &&     apt-get install -y --no-install-recommends     g  0.0s
 => CACHED [story-service builder 4/5] COPY services/story-service/requirements.txt .                              0.0s
 => CACHED [story-service builder 5/5] RUN pip install --no-cache-dir --user -r requirements.txt                   0.0s
 => CACHED [story-service stage-1 4/9] COPY --from=builder /root/.local /root/.local                               0.0s
 => CACHED [story-service stage-1 5/9] COPY shared/lib-logging /app/shared/lib-logging                             0.0s
 => CACHED [story-service stage-1 6/9] COPY shared/lib-tracing /app/shared/lib-tracing                             0.0s
 => CACHED [story-service stage-1 7/9] COPY shared/lib-config /app/shared/lib-config                               0.0s
 => CACHED [story-service stage-1 8/9] COPY services/story-service/src/ ./src/                                     0.0s
 => CACHED [story-service stage-1 9/9] RUN useradd -m -u 1000 appuser &&     chown -R appuser:appuser /app         0.0s
 => [story-service] exporting to image                                                                             0.2s
 => => exporting layers                                                                                            0.0s
 => => exporting manifest sha256:f3f7f0544deb79232a062f026ec41b0ec5a5697a62416502895c86e4a10ba53a                  0.0s
 => => exporting config sha256:d6619530c2d634c1cb6c33cf8dc44e784d17960eb0883a9da87e74037761a2f7                    0.0s
 => => exporting attestation manifest sha256:96d140aa3bed9a0a321f13ae73073b54044edbe6707cb5997b524b652754bd24      0.1s
 => => exporting manifest list sha256:94edcbd18828e7067f89848e8b764527b2f2c24ab9d10bfc548ea10b3339caf1             0.0s
 => => naming to docker.io/library/kidcomic-story-service:latest                                                   0.0s
 => => unpacking to docker.io/library/kidcomic-story-service:latest                                                0.0s
 => [story-service] resolving provenance for metadata file                                                         0.0s
[OK] Built Story Service image
Starting services...
[+] Running 18/18
 ✔ Network kidcomic_backend            Created                                                                     0.1s
 ✔ Network kidcomic_observability      Created                                                                     0.1s
 ✔ Volume "kidcomic_loki-data"         Created                                                                     0.0s
 ✔ Volume "kidcomic_traefik-logs-2"    Created                                                                     0.0s
 ✔ Volume "kidcomic_story-db-data"     Created                                                                     0.0s
 ✔ Volume "kidcomic_grafana-data"      Created                                                                     0.0s
 ✔ Volume "kidcomic_traefik-logs"      Created                                                                     0.0s
 ✔ Volume "kidcomic_prometheus-data"   Created                                                                     0.0s
 ✔ Volume "kidcomic_tempo-data"        Created                                                                     0.0s
 ✔ Container kidcomic-loki-1           Started                                                                     2.0s
 ✔ Container kidcomic-consul-1         Healthy                                                                     7.6s
 ✔ Container kidcomic-story-db-1       Healthy                                                                    12.6s
 ✔ Container kidcomic-tempo-1          Started                                                                     1.7s
 ✔ Container kidcomic-traefik-1-1      Started                                                                     2.7s
 ✔ Container kidcomic-story-service-1  Started                                                                    12.5s
 ✔ Container kidcomic-traefik-2-1      Started                                                                     2.2s
 ✔ Container kidcomic-prometheus-1     Started                                                                     2.0s
 ✔ Container kidcomic-grafana-1        Started                                                                     2.3s
[OK] Services started

Waiting for services to be healthy (90 seconds)...

=== Step 4: Verifying Service Health ===
Checking service status...
[FAIL]  is
[FAIL]  is
[FAIL]  is
[FAIL]  is
[FAIL] Only 0/4 services are healthy

Testing service endpoints...
[FAIL] Traefik Dashboard not accessible
[OK] Consul UI accessible (http://localhost:8500)
[FAIL] Prometheus not accessible
[OK] Grafana accessible (http://localhost:3001)
[FAIL] Story Service not accessible

Testing API Gateway routing...
[FAIL] Story Service not accessible via Gateway
Error: 無法連接至遠端伺服器

=== Step 5: Running Validation Tests (T044-T047) ===

T044: Running Contract Tests...
Running: pytest test_gateway_routing.py -v
C:\Python313\Lib\site-packages\pytest_asyncio\plugin.py:208: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
================================================= test session starts =================================================
platform win32 -- Python 3.13.7, pytest-8.3.3, pluggy-1.6.0 -- C:\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\kidcomic\tests\integration
plugins: anyio-4.11.0, asyncio-0.24.0, cov-6.0.0, mock-3.14.0
asyncio: mode=Mode.STRICT, default_loop_scope=None
collected 9 items

test_gateway_routing.py::TestGatewayRoutingContract::test_traefik_config_exists PASSED                           [ 11%]
test_gateway_routing.py::TestGatewayRoutingContract::test_story_service_route_exists PASSED                      [ 22%]
test_gateway_routing.py::TestGatewayRoutingContract::test_payment_service_route_exists PASSED                    [ 33%]
test_gateway_routing.py::TestGatewayRoutingContract::test_routing_rules_match_contract PASSED                    [ 44%]
test_gateway_routing.py::TestGatewayRoutingContract::test_health_endpoint_configured PASSED                      [ 55%]
test_gateway_routing.py::TestGatewayRoutingContract::test_metrics_endpoint_configured PASSED                     [ 66%]
test_gateway_routing.py::TestGatewayMiddleware::test_auth_middleware_exists PASSED                               [ 77%]
test_gateway_routing.py::TestGatewayMiddleware::test_rate_limit_middleware_exists PASSED                         [ 88%]
test_gateway_routing.py::TestGatewayMiddleware::test_rate_limit_default_10_req_per_sec PASSED                    [100%]

================================================== 9 passed in 0.07s ==================================================
[OK] T044: Contract tests PASSED

T045: Running End-to-End Tests...
Running: pytest test_gateway_e2e.py -v
C:\Python313\Lib\site-packages\pytest_asyncio\plugin.py:208: PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
The event loop scope for asynchronous fixtures will default to the fixture caching scope. Future versions of pytest-asyncio will default the loop scope for asynchronous fixtures to function scope. Set the default fixture loop scope explicitly in order to avoid unexpected behavior in the future. Valid fixture loop scopes are: "function", "class", "module", "package", "session"

  warnings.warn(PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET))
================================================= test session starts =================================================
platform win32 -- Python 3.13.7, pytest-8.3.3, pluggy-1.6.0 -- C:\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\kidcomic\tests\e2e
plugins: anyio-4.11.0, asyncio-0.24.0, cov-6.0.0, mock-3.14.0
asyncio: mode=Mode.STRICT, default_loop_scope=None
collected 10 items

test_gateway_e2e.py::TestGatewayE2E::test_gateway_is_accessible FAILED                                           [ 10%]
test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_health FAILED                                   [ 20%]
test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_ready FAILED                                    [ 30%]
test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_list FAILED                                     [ 40%]
test_gateway_e2e.py::TestGatewayE2E::test_trace_id_propagated_through_gateway FAILED                             [ 50%]
test_gateway_e2e.py::TestGatewayE2E::test_gateway_adds_latency_headers FAILED                                    [ 60%]
test_gateway_e2e.py::TestGatewayE2E::test_gateway_handles_404_correctly FAILED                                   [ 70%]
test_gateway_e2e.py::TestGatewayE2E::test_gateway_performance_baseline SKIPPED (Cannot run performance test ...) [ 80%]
test_gateway_e2e.py::TestGatewayHA::test_multiple_gateway_instances_configured SKIPPED (HA verification requ...) [ 90%]
test_gateway_e2e.py::TestGatewayHA::test_gateway_failover SKIPPED (Failover test requires infrastructure setup)  [100%]

====================================================== FAILURES =======================================================
______________________________________ TestGatewayE2E.test_gateway_is_accessible ______________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59BB6D010>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB6D010>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:36: in test_gateway_is_accessible
    response = requests.get(f"{gateway_url}/health", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB6D010>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:39: in test_gateway_is_accessible
    pytest.fail(f"Cannot connect to gateway at {gateway_url}")
E   Failed: Cannot connect to gateway at http://localhost:80
__________________________________ TestGatewayE2E.test_route_to_story_service_health __________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59C158A50>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59C158A50>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:48: in test_route_to_story_service_health
    response = requests.get(f"{gateway_url}/stories/health", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59C158A50>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:52: in test_route_to_story_service_health
    pytest.fail("Story service not reachable through gateway")
E   Failed: Story service not reachable through gateway
__________________________________ TestGatewayE2E.test_route_to_story_service_ready ___________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59C159590>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ready (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59C159590>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:61: in test_route_to_story_service_ready
    response = requests.get(f"{gateway_url}/stories/ready", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ready (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59C159590>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:64: in test_route_to_story_service_ready
    pytest.fail("Story service readiness not reachable through gateway")
E   Failed: Story service readiness not reachable through gateway
___________________________________ TestGatewayE2E.test_route_to_story_service_list ___________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59BB8E3F0>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB8E3F0>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:73: in test_route_to_story_service_list
    response = requests.get(f"{gateway_url}/stories/", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB8E3F0>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:81: in test_route_to_story_service_list
    pytest.fail("Story service list not reachable through gateway")
E   Failed: Story service list not reachable through gateway
_______________________________ TestGatewayE2E.test_trace_id_propagated_through_gateway _______________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59BB8DF30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB8DF30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:93: in test_trace_id_propagated_through_gateway
    response = requests.get(f"{gateway_url}/stories/", headers=headers, timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB8DF30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:100: in test_trace_id_propagated_through_gateway
    pytest.fail("Cannot test trace_id propagation - service not reachable")
E   Failed: Cannot test trace_id propagation - service not reachable
__________________________________ TestGatewayE2E.test_gateway_adds_latency_headers ___________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59BB9A210>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB9A210>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:108: in test_gateway_adds_latency_headers
    response = requests.get(f"{gateway_url}/stories/health", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /stories/health (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BB9A210>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:113: in test_gateway_adds_latency_headers
    pytest.fail("Cannot test headers - service not reachable")
E   Failed: Cannot test headers - service not reachable
__________________________________ TestGatewayE2E.test_gateway_handles_404_correctly __________________________________
C:\Python313\Lib\site-packages\urllib3\connection.py:198: in _new_conn
    sock = connection.create_connection(
C:\Python313\Lib\site-packages\urllib3\util\connection.py:85: in create_connection
    raise err
C:\Python313\Lib\site-packages\urllib3\util\connection.py:73: in create_connection
    sock.connect(sa)
E   ConnectionRefusedError: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:787: in urlopen
    response = self._make_request(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:493: in _make_request
    conn.request(
C:\Python313\Lib\site-packages\urllib3\connection.py:494: in request
    self.endheaders()
C:\Python313\Lib\http\client.py:1333: in endheaders
    self._send_output(message_body, encode_chunked=encode_chunked)
C:\Python313\Lib\http\client.py:1093: in _send_output
    self.send(msg)
C:\Python313\Lib\http\client.py:1037: in send
    self.connect()
C:\Python313\Lib\site-packages\urllib3\connection.py:325: in connect
    self.sock = self._new_conn()
C:\Python313\Lib\site-packages\urllib3\connection.py:213: in _new_conn
    raise NewConnectionError(
E   urllib3.exceptions.NewConnectionError: <urllib3.connection.HTTPConnection object at 0x000002A59BC34F30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。

The above exception was the direct cause of the following exception:
C:\Python313\Lib\site-packages\requests\adapters.py:644: in send
    resp = conn.urlopen(
C:\Python313\Lib\site-packages\urllib3\connectionpool.py:841: in urlopen
    retries = retries.increment(
C:\Python313\Lib\site-packages\urllib3\util\retry.py:519: in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
E   urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /nonexistent (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BC34F30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:122: in test_gateway_handles_404_correctly
    response = requests.get(f"{gateway_url}/nonexistent", timeout=5)
C:\Python313\Lib\site-packages\requests\api.py:73: in get
    return request("get", url, params=params, **kwargs)
C:\Python313\Lib\site-packages\requests\api.py:59: in request
    return session.request(method=method, url=url, **kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:589: in request
    resp = self.send(prep, **send_kwargs)
C:\Python313\Lib\site-packages\requests\sessions.py:703: in send
    r = adapter.send(request, **kwargs)
C:\Python313\Lib\site-packages\requests\adapters.py:677: in send
    raise ConnectionError(e, request=request)
E   requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=80): Max retries exceeded with url: /nonexistent (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002A59BC34F30>: Failed to establish a new connection: [WinError 10061] 無法連線，因為目標電腦拒絕連線。'))

During handling of the above exception, another exception occurred:
test_gateway_e2e.py:125: in test_gateway_handles_404_correctly
    pytest.fail("Gateway not responding for 404 test")
E   Failed: Gateway not responding for 404 test
=============================================== short test summary info ===============================================
FAILED test_gateway_e2e.py::TestGatewayE2E::test_gateway_is_accessible - Failed: Cannot connect to gateway at http://localhost:80
FAILED test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_health - Failed: Story service not reachable through gateway
FAILED test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_ready - Failed: Story service readiness not reachable through gateway
FAILED test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_list - Failed: Story service list not reachable through gateway
FAILED test_gateway_e2e.py::TestGatewayE2E::test_trace_id_propagated_through_gateway - Failed: Cannot test trace_id propagation - service not reachable
FAILED test_gateway_e2e.py::TestGatewayE2E::test_gateway_adds_latency_headers - Failed: Cannot test headers - service not reachable
FAILED test_gateway_e2e.py::TestGatewayE2E::test_gateway_handles_404_correctly - Failed: Gateway not responding for 404 test
============================================ 7 failed, 3 skipped in 33.48s ============================================
[FAIL] T045: E2E tests FAILED

T046: Running Load Tests...
Running: k6 run test_gateway_load.js

         /\      Grafana   /‾‾/
    /\  /  \     |\  __   /  /
   /  \/    \    | |/ /  /   ‾‾\
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/

     execution: local
        script: test_gateway_load.js
        output: -

     scenarios: (100.00%) 1 scenario, 100 max VUs, 5m30s max duration (incl. graceful stop):
              * default: Up to 100 looping VUs for 5m0s over 5 stages (gracefulRampDown: 30s, gracefulStop: 30s)

INFO[0000] Starting load test...                         source=console
INFO[0000] Target: http://localhost:80                   source=console
WARN[0000] Request Failed                                error="Get \"http://localhost:80/stories/health\": dial tcp 127.0.0.1:80: connectex: No connection could be made because the target machine actively refused it."
ERRO[0000] Gateway not accessible! Aborting test.        source=console


  █ THRESHOLDS

    errors
    ✓ 'rate<0.01' rate=0.00%

    http_req_duration
    ✓ 'p(95)<50' p(95)=0s

    http_req_failed
    ✗ 'rate<0.01' rate=100.00%


  █ TOTAL RESULTS

    CUSTOM
    errors..............: 0.00%   0 out of 0

    HTTP
    http_req_duration...: avg=0s min=0s med=0s max=0s p(90)=0s p(95)=0s
    http_req_failed.....: 100.00% 1 out of 1
    http_reqs...........: 1       236.473704/s

    NETWORK
    data_received.......: 0 B     0 B/s
    data_sent...........: 0 B     0 B/s




Run       [======================================] setup()
default   [--------------------------------------]
ERRO[0000] Error: Gateway health check failed
        at setup (file:///D:/kidcomic/tests/load/test_gateway_load.js:118:11(34))  hint="script exception"
[FAIL] T046: Load tests FAILED

T047: Verifying Error Handling...
[OK] T047: Error handling verification PASSED

=== Step 6: Generating Validation Report ===

========================================
         VALIDATION SUMMARY
========================================
Total Tests:   16
Passed:        9
Failed:        7
Warnings:      0
Skipped:       0
Duration:      179.95 seconds
========================================

[OK] Validation report saved to: VALIDATION_RESULTS_2025-12-06_05-41-29.md


========================================
         DEPLOYMENT COMPLETE
========================================

Dashboards:
   - Traefik:    http://localhost:8088/dashboard/
   - Grafana:    http://localhost:3001 (admin/admin)
   - Prometheus: http://localhost:9090
   - Consul:     http://localhost:8500

Test API:
   curl http://localhost/stories/

Full Report:
   VALIDATION_RESULTS_2025-12-06_05-41-29.md

Documentation:
   - Deployment: MVP_DEPLOYMENT_GUIDE.md
   - Summary:    MVP_IMPLEMENTATION_SUMMARY.md
   - Runbook:    infrastructure/ci-cd/runbooks/gateway-failover.md

========================================

PS D:\kidcomic> docker-compose ps
NAME                  IMAGE                     COMMAND                   SERVICE    CREATED         STATUS                   PORTS
kidcomic-consul-1     hashicorp/consul:latest   "docker-entrypoint.s…"   consul     9 minutes ago   Up 9 minutes (healthy)   8300-8302/tcp, 8600/tcp, 8301-8302/udp, 0.0.0.0:8500->8500/tcp, 0.0.0.0:8600->8600/udp
kidcomic-grafana-1    grafana/grafana:latest    "/run.sh"                 grafana    9 minutes ago   Up 9 minutes             0.0.0.0:3001->3000/tcp
kidcomic-story-db-1   postgres:15-alpine        "docker-entrypoint.s…"   story-db   9 minutes ago   Up 9 minutes (healthy)   0.0.0.0:5433->5432/tcp
kidcomic-tempo-1      grafana/tempo:latest      "/tempo -config.file…"   tempo      9 minutes ago   Up 9 minutes             0.0.0.0:3200->3200/tcp, 0.0.0.0:4317->4317/tcp
PS D:\kidcomic>