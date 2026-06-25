# Agent Registry

Updated: 2026-06-18 12:00 SEAST

| Agent/Profile | Purpose | Skills/Capabilities | Location | Status |
|---|---|---|---|---|
| default | Orchestrator / commander | User chat, Telegram gateway, Kanban dispatcher, task routing, final reporting | Hermes default profile | active gateway |
| hermesbuilder | Builder / coder | Code edits, tests, implementation, repo fixes | Hermes profile `hermesbuilder` | kanban worker standby |
| hermesreviewer | Reviewer / QA | Diff review, validation, risk checks, acceptance review | Hermes profile `hermesreviewer` | kanban worker standby |
| hermesops | Ops / health | Runtime checks, gateway/cron/MT5/host health, deployment risk | Hermes profile `hermesops` | kanban worker standby |
| atsawin-autonomous | Long-running maintenance / cron worker | Scheduled reports/watchdog, readiness checks | Hermes profile `atsawin-autonomous` | cron worker standby; profile gateway stopped |
| Memory Loader | Load/update memory docs | spec/architecture/system_state/hot knowledge sync | repos/AI/*.md | active pattern |
| Project Scanner | Analyze workspace structure and critical modules | file tree, API/module mapping, config discovery | repos/AI | active pattern |

## Operating rules
- Use Kanban for durable multi-agent work: default creates tasks, worker profiles execute.
- Keep only the default gateway polling Telegram unless each profile has a separate bot token.
- Worker profile gateways stay stopped by default; the default gateway embedded dispatcher or manual `hermes kanban dispatch` can spawn workers.
- Start small: builder + reviewer + ops. Add more specialists only after the workflow is stable.
- Keep memory/skills minimal at first to avoid context bloat; add focused skills only when a task requires them.
