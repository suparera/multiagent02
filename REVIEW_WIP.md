# review_wip.md

# Review / Re-Review Observations

## Current Finding

The re-review results are not identical to the first review results.

This does NOT necessarily mean:
- the fixer failed
- the original problems still exist

In many cases:
- the reviewer shifted focus
- previously critical issues were fixed
- deeper issues became visible afterward

---

# What Happened

## First Review

Reviewer focused on:
- authorization
- IDOR
- validation
- financial precision
- dangerous configuration

Examples:
- BROKEN_ACCESS_CONTROL
- INSECURE_DIRECT_OBJECT_REFERENCE
- MISSING_BUSINESS_VALIDATION

---

## After Fixer

The fixer likely resolved several major issues.

During re-review:
- reviewer attention moved to infrastructure/runtime concerns

Examples:
- Kafka bootstrap servers
- Kafka consumer groups
- timezone consistency
- missing indexes
- DLQ strategy
- datasource credentials

This behavior is normal.

---

# Important Concept

This phenomenon is:

## "Review Frontier Expansion"

As obvious issues disappear:
- reviewers begin noticing subtler or deeper issues

Very similar to:
- human code reviews
- PCI audit rounds
- penetration testing phases
- SonarQube cleanup iterations

---

# Key Realization

AI review systems are NOT fully deterministic.

Two review passes may:
- focus on different layers
- prioritize different risks
- surface different findings

Even with nearly identical code.

---

# Current Weakness

Current architecture uses:
- one large generic reviewer

This causes:
- attention drift
- unstable findings
- inconsistent focus

---

# Recommended Evolution

Move toward specialized reviewers.

Examples:
- SecurityReviewer
- InfraReviewer
- ConcurrencyReviewer
- PerformanceReviewer
- APIReviewer

Each reviewer should:
- focus on one concern only
- use narrower prompts
- review smaller code scopes

---

# Better Future Architecture

Instead of:

review(huge_blob)

Move toward:

review_file("Order.java")
review_file("KafkaConfig.java")
review_file("application.yml")

This improves:
- determinism
- stability
- reproducibility
- latency

---

# Important Insight

AI orchestration is NOT mostly prompting.

The real complexity is:
- context management
- failure handling
- normalization
- reviewer stability
- specialization
- routing
- state management

---

# Practical Next Step

Implement:

## Review Delta Analysis

Compare:
- first review
- re-review

Output categories:

### FIXED
Issues that disappeared after fixes.

### NEW
Issues introduced or newly discovered.

### REMAINING
Issues still present after fixing.

This will make the orchestration loop much more understandable.

---

# Current System Capabilities

The orchestration system already demonstrates:

- iterative repair loops
- multi-agent workflows
- review/fix/re-review cycles
- failure handling
- provider abstraction
- failover routing concepts
- emergent reviewer specialization needs

This is moving beyond simple prompting into real orchestration engineering.
