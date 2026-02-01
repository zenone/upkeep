# Security Documentation - Mac Maintenance

**Last Updated**: 2026-01-28
**Status**: 🟡 BASELINE ESTABLISHED - AUDIT PENDING
**Compliance**: OWASP Top 10 (2021)

---

## 🔒 Threat Model

### System Overview
Mac Maintenance is a **privileged system utility** that:
- Executes root-level operations (cache clearing, disk repair, Homebrew updates)
- Accepts user input via Web UI and TUI
- Bridges Python and Bash code
- Runs a persistent daemon with elevated privileges

### Trust Boundaries
```
┌─────────────────────────────────────────────────┐
│ User (Untrusted)                                │
│   ↓ HTTP Requests                               │
│ ┌─────────────────────────────────────────────┐ │
│ │ Web Server (User-level process)             │ │
│ │   • FastAPI                                 │ │
│ │   • Input validation                        │ │
│ │   • No root privileges                      │ │
│ └─────────────────────────────────────────────┘ │
│   ↓ IPC (HTTP REST)                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ Daemon (Root-level process)                 │ │
│ │   • Executes privileged operations          │ │
│ │   • Validates job queue                     │ │
│ │   • Logs all actions                        │ │
│ └─────────────────────────────────────────────┘ │
│   ↓ Shell Execution                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ System (macOS)                              │ │
│ │   • Bash scripts (maintain.sh)              │ │
│ │   • Homebrew, system caches, permissions    │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 🛡️ OWASP Top 10 (2021) - Current Posture

### A01:2021 – Broken Access Control
**Risk**: 🟡 MEDIUM
**Status**: PARTIALLY MITIGATED

**Concerns**:
- Daemon has no authentication (trusts all localhost requests)
- Web server has no user authentication

**Current Mitigations**:
- Daemon only listens on `localhost` (not exposed to network)
- Web server binds to `127.0.0.1:8080`

**Planned Fixes** (Phase 4+):
- [ ] Add daemon API token authentication
- [ ] Add session-based auth for web UI (optional for single-user systems)

---

### A02:2021 – Cryptographic Failures
**Risk**: 🟢 LOW
**Status**: NOT APPLICABLE

**Rationale**:
- No sensitive data stored (no passwords, credit cards, PII)
- No network transmission of secrets
- Job queue uses local filesystem

---

### A03:2021 – Injection
**Risk**: 🔴 HIGH
**Status**: ⚠️ NEEDS AUDIT

**Concerns**:
1. **Command Injection**: User input passed to shell scripts
2. **Path Traversal**: File deletion operations accept user-provided paths

**Current Mitigations**:
- Limited operation set (predefined maintenance tasks)
- No direct shell command input from users

**Required Actions** (Phase 1 - Security Audit):
- [x] Audit all `subprocess.run()` calls for shell injection
- [ ] Validate all file paths against allowlist
- [ ] Sanitize inputs in `src/mac_maintenance/web/server.py`
- [ ] Add input validation tests

**Known Vulnerable Code Paths**:
```python
# NEEDS REVIEW: src/mac_maintenance/core/system.py
# NEEDS REVIEW: src/mac_maintenance/bridge.py
# NEEDS REVIEW: maintain.sh (all functions)
```

---

### A04:2021 – Insecure Design
**Risk**: 🟡 MEDIUM
**Status**: UNDER REVIEW

**Concerns**:
- Daemon restart requires manual intervention
- No rate limiting on API endpoints
- No audit logging for privileged operations

**Planned Fixes** (Phase 1.2):
- [ ] Add structured audit logging
- [ ] Implement API rate limiting (10 req/sec per endpoint)
- [ ] Add daemon health checks and auto-restart

---

### A05:2021 – Security Misconfiguration
**Risk**: 🟡 MEDIUM
**Status**: PARTIALLY MITIGATED

**Concerns**:
- Debug logging enabled in production code
- No Content-Security-Policy headers
- No HTTPS (localhost only, acceptable for v1)

**Current State**:
- ✅ Daemon runs with minimal required privileges
- ❌ Debug mode still active (`window.DEBUG = true`)

**Planned Fixes** (Phase 5):
- [ ] Remove debug logging from production
- [ ] Add CSP headers to web server
- [ ] Add security.txt file

---

### A06:2021 – Vulnerable and Outdated Components
**Risk**: 🟢 LOW
**Status**: MONITORED

**Current Dependencies**:
- FastAPI: Latest
- Textual: Latest
- Python: 3.11+

**Required Actions** (Phase 1.2):
- [ ] Add `pip-audit` to CI/CD pipeline
- [ ] Add `dependabot` or equivalent
- [ ] Document update policy

---

### A07:2021 – Identification and Authentication Failures
**Risk**: 🟡 MEDIUM
**Status**: DEFERRED

**Rationale**:
- Single-user system (macOS laptop)
- Physical access = authorized access

**Future Consideration** (Phase 4+):
- [ ] Add optional password protection for web UI
- [ ] Add daemon API token

---

### A08:2021 – Software and Data Integrity Failures
**Risk**: 🟡 MEDIUM
**Status**: NEEDS IMPLEMENTATION

**Concerns**:
- No code signing
- No checksum verification for downloaded updates

**Planned Fixes** (Post-MVP):
- [ ] Sign daemon binary
- [ ] Verify Homebrew updates before applying

---

### A09:2021 – Security Logging and Monitoring Failures
**Risk**: 🔴 HIGH
**Status**: ⚠️ CRITICAL GAP

**Current State**:
- ❌ No centralized audit log
- ❌ No alerting for suspicious activity
- ❌ No retention policy

**Required Actions** (Phase 1.2):
- [ ] Create `/var/log/mac-maintenance/audit.log`
- [ ] Log all privileged operations (who, what, when, result)
- [ ] Add log rotation (7-day retention)

**Log Format**:
```json
{
  "timestamp": "2026-01-28T17:35:00Z",
  "user": "szenone",
  "operation": "clear_system_caches",
  "status": "success",
  "duration_ms": 2300,
  "ip": "127.0.0.1"
}
```

---

### A10:2021 – Server-Side Request Forgery (SSRF)
**Risk**: 🟢 LOW
**Status**: NOT APPLICABLE

**Rationale**:
- No outbound HTTP requests from user input
- No URL fetching functionality

---

## 🔍 Vulnerability Scan Log

### Scan #1 - 2026-01-28 (Baseline)
**Method**: Manual code review
**Scope**: All Python and Bash files
**Findings**: 0 (audit pending)

**Next Scan**: After Phase 1.1 completion

---

## 📋 Security Checklist (Pre-Ship)

Before any public release:
- [ ] All OWASP Top 10 items rated 🟢 LOW or MITIGATED
- [ ] Input validation on 100% of user-facing endpoints
- [ ] Audit logging enabled and tested
- [ ] Dependency scan clean (no known CVEs)
- [ ] Code review by Security/SRE agent
- [ ] Penetration test (basic fuzzing)

---

## 🚨 Incident Response

### Stop-Ship Authority
**Security/SRE Agent** holds veto power on any commit that:
- Introduces a new command injection vector
- Disables existing security controls
- Exposes privileged operations without validation

### Emergency Contact
**Owner**: szenone
**Escalation**: File issue in GitHub repository

---

## 📚 References

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [CWE Top 25 (2023)](https://cwe.mitre.org/top25/)
- [macOS Security Guide](https://support.apple.com/guide/security/welcome/web)

---

**Next Review Date**: 2026-02-01 (after Phase 1 completion)
