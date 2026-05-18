# AGENT CONTRACTS

## Interface Definitions for Multi-Agent Communication

---

## 1. Agent Registration Contract

### Register Agent
```
POST /agent/register
Request:
{
    "agent_id": string,
    "agent_type": "coding" | "trading" | "monitoring" | "research" | "coordination",
    "capabilities": string[],
    "max_concurrent_tasks": int
}
Response:
{
    "status": "registered",
    "agent_id": string,
    "registered_at": ISO8601 timestamp
}
```

### Unregister Agent
```
POST /agent/unregister/{agent_id}
Response:
{
    "status": "unregistered",
    "agent_id": string
}
```

---

## 2. Task Management Contract

### Submit Task
```
POST /agent/task/submit
Request:
{
    "task_type": string,
    "required_capabilities": string[],
    "task_data": object,
    "priority": "low" | "normal" | "high" | "critical",
    "deadline": ISO8601 timestamp (optional),
    "dependencies": string[] (optional)
}
Response:
{
    "task_id": string,
    "status": "submitted",
    "assigned_agent": string | null
}
```

### Get Task Status
```
GET /agent/task/{task_id}
Response:
{
    "task_id": string,
    "status": "pending" | "assigned" | "in_progress" | "completed" | "failed" | "cancelled",
    "assigned_agent": string | null,
    "progress": float (0.0 - 1.0),
    "result": object | null,
    "error_message": string | null,
    "created_at": ISO8601 timestamp,
    "updated_at": ISO8601 timestamp
}
```

### Cancel Task
```
POST /agent/task/{task_id}/cancel
Response:
{
    "task_id": string,
    "status": "cancelled"
}
```

---

## 3. Agent Communication Contract

### Send Message (Agent-to-Agent)
```
POST /agent/message/send
Request:
{
    "source_agent": string,
    "target_agent": string,
    "message_type": "task_request" | "task_response" | "coordination" | "status_update" | "alert",
    "priority": "low" | "normal" | "high" | "critical",
    "data": object
}
Response:
{
    "message_id": string,
    "delivered": boolean,
    "timestamp": ISO8601 timestamp
}
```

### Get Message History
```
GET /agent/message/history?agent_id={id}&limit={n}
Response:
{
    "messages": [
        {
            "message_id": string,
            "source_agent": string,
            "target_agent": string,
            "message_type": string,
            "data": object,
            "timestamp": ISO8601 timestamp
        }
    ],
    "total": int
}
```

---

## 4. Agent State Contract

### Get Agent State
```
GET /agent/state/{agent_id}
Response:
{
    "agent_id": string,
    "status": "idle" | "busy" | "offline" | "error",
    "current_tasks": string[],
    "load_score": float (0.0 - 1.0),
    "capabilities": string[],
    "last_heartbeat": ISO8601 timestamp,
    "uptime_seconds": int
}
```

### Update Agent Heartbeat
```
POST /agent/heartbeat/{agent_id}
Request:
{
    "status": string,
    "load_score": float,
    "current_tasks": string[]
}
Response:
{
    "acknowledged": boolean,
    "timestamp": ISO8601 timestamp
}
```

---

## 5. Coordination Contract

### Submit Coordinated Task
```
POST /agent/coordinated-task
Request:
{
    "main_task": string,
    "sub_tasks": [
        {
            "task_type": string,
            "required_capabilities": string[],
            "task_data": object,
            "dependencies": string[]
        }
    ],
    "priority": "low" | "normal" | "high" | "critical"
}
Response:
{
    "coordination_id": string,
    "task_ids": string[],
    "status": "submitted"
}
```

### Get Coordination Status
```
GET /agent/coordination/{coordination_id}
Response:
{
    "coordination_id": string,
    "overall_status": string,
    "tasks": [
        {
            "task_id": string,
            "status": string,
            "assigned_agent": string,
            "progress": float
        }
    ],
    "completion_percentage": float
}
```

---

## 6. Conflict Resolution Contract

### Report Conflict
```
POST /agent/conflict/report
Request:
{
    "task_id": string,
    "conflict_type": "resource" | "dependency" | "priority" | "capability",
    "description": string,
    "involved_agents": string[]
}
Response:
{
    "conflict_id": string,
    "resolution": "reassigned" | "queued" | "split" | "escalated",
    "resolved_at": ISO8601 timestamp
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 4001 | Agent not found |
| 4002 | Task not found |
| 4003 | Agent unavailable |
| 4004 | Capability mismatch |
| 4005 | Task dependency not met |
| 4006 | Conflict detected |
| 4007 | Invalid task state transition |
| 4008 | Message delivery failed |
| 4009 | Coordination timeout |
| 4010 | Rate limit exceeded |
