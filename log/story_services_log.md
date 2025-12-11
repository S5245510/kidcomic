2025-12-06 07:39:17 Traceback (most recent call last):
2025-12-06 07:39:17   File "/home/appuser/.local/bin/uvicorn", line 8, in <module>
2025-12-06 07:39:17     sys.exit(main())
2025-12-06 07:39:17              ^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
2025-12-06 07:39:17     return self.main(*args, **kwargs)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1406, in main
2025-12-06 07:39:17     rv = self.invoke(ctx)
2025-12-06 07:39:17          ^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
2025-12-06 07:39:17     return ctx.invoke(self.callback, **ctx.params)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/click/core.py", line 824, in invoke
2025-12-06 07:39:17     return callback(*args, **kwargs)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 418, in main
2025-12-06 07:39:17     run(
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/main.py", line 587, in run
2025-12-06 07:39:17     server.run()
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 62, in run
2025-12-06 07:39:17     return asyncio.run(self.serve(sockets=sockets))
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
2025-12-06 07:39:17     return runner.run(main)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
2025-12-06 07:39:17     return self._loop.run_until_complete(task)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/server.py", line 69, in serve
2025-12-06 07:39:17     config.load()
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/config.py", line 458, in load
2025-12-06 07:39:17     self.loaded_app = import_from_string(self.app)
2025-12-06 07:39:17                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 24, in import_from_string
2025-12-06 07:39:17     raise exc from None
2025-12-06 07:39:17   File "/home/appuser/.local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
2025-12-06 07:39:17     module = importlib.import_module(module_str)
2025-12-06 07:39:17              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
2025-12-06 07:39:17     return _bootstrap._gcd_import(name[level:], package, level)
2025-12-06 07:39:17            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-06 07:39:17   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
2025-12-06 07:39:17   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
2025-12-06 07:39:17   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
2025-12-06 07:39:17   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
2025-12-06 07:39:17   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2025-12-06 07:39:17   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
2025-12-06 07:39:17   File "/app/src/main.py", line 21, in <module>
2025-12-06 07:39:17     from lib_logging.src.logger import configure_logging, get_logger, get_logger_with_trace
2025-12-06 07:39:17 ModuleNotFoundError: No module named 'lib_logging'