2025-12-06 07:32:00 time=2025-12-05T21:32:00.232Z level=INFO source=main.go:1557 msg="updated GOGC" old=100 new=75
2025-12-06 07:32:00 time=2025-12-05T21:32:00.234Z level=INFO source=main.go:688 msg="Leaving GOMAXPROCS=12: CPU quota undefined" component=automaxprocs
2025-12-06 07:32:00 time=2025-12-05T21:32:00.235Z level=INFO source=memlimit.go:198 msg="GOMEMLIMIT is updated" component=automemlimit package=github.com/KimMachineGun/automemlimit/memlimit GOMEMLIMIT=15013800345 previous=9223372036854775807
2025-12-06 07:32:00 time=2025-12-05T21:32:00.235Z level=INFO source=main.go:781 msg="Starting Prometheus Server" mode=server version="(version=3.8.0, branch=HEAD, revision=e44ed351cdf0181f9fde56ba096f4d949f9e295d)"
2025-12-06 07:32:00 time=2025-12-05T21:32:00.235Z level=INFO source=main.go:786 msg="operational information" build_context="(go=go1.25.4, platform=linux/amd64, user=root@e0c39c41863e, date=20251202-09:08:25, tags=netgo,builtinassets)" host_details="(Linux 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025 x86_64 10b642108a21 localdomain)" fd_limits="(soft=1048576, hard=1048576)" vm_limits="(soft=unlimited, hard=unlimited)"
2025-12-06 07:32:00 time=2025-12-05T21:32:00.243Z level=INFO source=web.go:663 msg="Start listening for connections" component=web address=0.0.0.0:9090
2025-12-06 07:32:00 time=2025-12-05T21:32:00.246Z level=INFO source=main.go:1301 msg="Starting TSDB ..."
2025-12-06 07:32:00 time=2025-12-05T21:32:00.249Z level=INFO source=tls_config.go:354 msg="Listening on" component=web address=[::]:9090
2025-12-06 07:32:00 time=2025-12-05T21:32:00.249Z level=INFO source=tls_config.go:357 msg="TLS is disabled." component=web http2=false address=[::]:9090
2025-12-06 07:32:00 time=2025-12-05T21:32:00.260Z level=INFO source=head.go:666 msg="Replaying on-disk memory mappable chunks if any" component=tsdb
2025-12-06 07:32:00 time=2025-12-05T21:32:00.264Z level=INFO source=head.go:752 msg="On-disk memory mappable chunks replay completed" component=tsdb duration=4.466µs
2025-12-06 07:32:00 time=2025-12-05T21:32:00.264Z level=INFO source=head.go:760 msg="Replaying WAL, this may take a while" component=tsdb
2025-12-06 07:32:00 time=2025-12-05T21:32:00.271Z level=INFO source=head.go:833 msg="WAL segment loaded" component=tsdb segment=0 maxSegment=0 duration=4.238061ms
2025-12-06 07:32:00 time=2025-12-05T21:32:00.271Z level=INFO source=head.go:870 msg="WAL replay completed" component=tsdb checkpoint_replay_duration=2.59719ms wal_replay_duration=4.276734ms wbl_replay_duration=121ns chunk_snapshot_load_duration=0s mmap_chunk_replay_duration=4.466µs total_replay_duration=6.898213ms
2025-12-06 07:32:00 time=2025-12-05T21:32:00.272Z level=INFO source=main.go:1322 msg="filesystem information" fs_type=EXT4_SUPER_MAGIC
2025-12-06 07:32:00 time=2025-12-05T21:32:00.272Z level=INFO source=main.go:1325 msg="TSDB started"
2025-12-06 07:32:00 time=2025-12-05T21:32:00.272Z level=INFO source=main.go:1510 msg="Loading configuration file" filename=/etc/prometheus/prometheus.yml
2025-12-06 07:32:00 time=2025-12-05T21:32:00.283Z level=INFO source=main.go:1550 msg="Completed loading of configuration file" db_storage=1.467µs remote_storage=1.122µs web_handler=656ns query_engine=876ns scrape=1.107961ms scrape_sd=670.399µs notify=1.29µs notify_sd=599ns rules=6.608681ms tracing=4.64µs filename=/etc/prometheus/prometheus.yml totalDuration=10.802644ms
2025-12-06 07:32:00 time=2025-12-05T21:32:00.283Z level=INFO source=main.go:1286 msg="Server is ready to receive web requests."
2025-12-06 07:32:00 time=2025-12-05T21:32:00.283Z level=INFO source=manager.go:190 msg="Starting rule manager..." component="rule manager"