# Security hardening review — 2026-10-16

Baseline: `eaf820666d15bfd545129f3223e2261c27191e74`.

## Changes and evidence

- Restore certificate-chain and hostname verification in the account checker and site submitter. Pass the validating context to both direct and explicit proxy connectors. Eight real loopback HTTPS tests cover trusted, untrusted, expired and wrong-host certificates for both clients; six negative cases failed before the fix. Proxy connectors share the context, but a live proxy tunnel was not exercised.
- Reject cross-origin browser writes using Origin, Referer and Fetch Metadata. Four hostile request cases failed before the fix; legitimate same-origin settings updates still work. Redirect settings responses only to a local path.
- Render site-picker names with textContent and dataset rather than interpolating HTML. A Node.js test executes the actual template functions against a minimal DOM; this is not a full-browser penetration test.
- Stop PDF resource fetching altogether. A preflight DNS check cannot constrain a later downloader's redirects or DNS rebinding. Profile images now use the bundled blank placeholder, including public image URLs. HTML reports retain their existing behavior.
- Neutralize formula prefixes in CSV fields, including whitespace-prefixed formulas. Seven malicious-cell cases failed before the change and pass after it. This changes the CSV representation of these values by adding an apostrophe.

## Validation

Focused command (Windows, Python 3.11):

```text
python -m pytest tests/test_tls_security.py tests/test_web_security.py tests/test_site_picker_security.py tests/test_pdf_resource_security.py tests/test_csv_security.py tests/test_checking.py tests/test_submit.py tests/test_web.py tests/test_report.py -m "not slow" -q --basetemp=../pytest-maigret-final2
```

Result: **231 passed, 1 skipped, 12 deselected**. The new tests include real local TLS handshakes and no external username searches. `trustme` is a development-only dependency; the Poetry lock was refreshed without updating existing package versions.

`pip-audit` reported no known vulnerabilities for the 108 pinned lockfile entries and the 127-package final test environment (editable project code is excluded from dependency auditing). This is a point-in-time advisory check, not a vulnerability-free guarantee. The environment's old pip/setuptools were upgraded locally, not through application dependency changes.

The wider test suite has pre-existing Windows/environment issues. `test_maigret.py` fails collection because `os.geteuid` is unavailable on Windows. Four other failing tests were rerun on the unmodified baseline and also failed: POSIX cache permissions, webgate error wording, slash-specific path assertions and executor timing/order. They were not silently rewritten or counted as successful.

## Review boundaries and residual risks

Reviewed network/TLS configuration, proxy and activation paths, dynamic execution/deserialization matches, report rendering/export paths, database update verification and GitHub workflows. Static analysis findings were manually triaged: the SHA1 computation is a remote protocol's signing algorithm, Markup wraps escaped content, and the XML parser validates a locally generated XMind manifest. These observations are not a dependency-source audit.

The web UI remains a local, unauthenticated tool. Origin checks are not authentication and intentionally permit non-browser clients without browser metadata. Do not expose it as an authenticated multi-user service; DNS-rebinding/Host defenses and rate/resource limits were not implemented. The existing predictable report directory remains a concern on shared hosts; configure a private REPORTS_FOLDER. Site databases and activation endpoints remain trusted configuration. HTML reports may load external resources. CSV behavior was checked as exported data, not by launching Excel. No production deployment, adversarial public-site tests or exhaustive fuzzing was performed.
