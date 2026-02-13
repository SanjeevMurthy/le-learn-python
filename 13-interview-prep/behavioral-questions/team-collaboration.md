# Behavioral Questions: Team Collaboration

## Story 1: Cross-Team Platform Migration

**Situation**: Migrating 15 microservices from EC2 to Kubernetes. Required coordination between 4 engineering teams.

**Task**: Lead the migration as the platform engineer without direct authority over app teams.

**Action**:

1. Created migration playbook with step-by-step guide
2. Held weekly migration office hours for support
3. Built migration tooling (Dockerfile generator, K8s manifest templates)
4. Migrated one service as a reference implementation
5. Paired with each team for their first migration

**Result**: All 15 services migrated in 8 weeks (target was 12 weeks). Zero production incidents during migration.

---

## Story 2: Implementing On-Call Culture

**Situation**: No formal on-call rotation. Production issues relied on "whoever noticed it." Response times were 30+ minutes.

**Task**: Establish an on-call process that developers would accept (not just SRE-imposed).

**Action**:

1. Proposed shared on-call model: developers on-call for their services
2. Created runbooks for every service's common failure modes
3. Set up PagerDuty with escalation policies
4. Established on-call handoff meetings and weekly incident reviews
5. Introduced "on-call compensation" to leadership

**Result**: Mean time to respond dropped from 30 min to 5 min. Developers gained production ownership. Reduced repeat incidents by 40%.

---

## Tips

- Demonstrate leadership without authority (influence, not mandate)
- Show empathy and understanding of other teams' constraints
- Highlight documentation and tooling as force multipliers
