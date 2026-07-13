from enum import Enum


class OrchestrationState(str, Enum):
    IDLE = "idle"
    ORCHESTRATING = "orchestrating"
    DISPATCHING = "dispatching"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


VALID_TRANSITIONS: dict[OrchestrationState, set[OrchestrationState]] = {
    OrchestrationState.IDLE: {OrchestrationState.ORCHESTRATING},
    OrchestrationState.ORCHESTRATING: {OrchestrationState.DISPATCHING, OrchestrationState.FAILED},
    OrchestrationState.DISPATCHING: {OrchestrationState.EXECUTING},
    OrchestrationState.EXECUTING: {OrchestrationState.REVIEWING, OrchestrationState.ORCHESTRATING, OrchestrationState.FAILED},
    OrchestrationState.REVIEWING: {OrchestrationState.TESTING, OrchestrationState.ORCHESTRATING},
    OrchestrationState.TESTING: {OrchestrationState.COMPLETED, OrchestrationState.ORCHESTRATING},
    OrchestrationState.COMPLETED: {OrchestrationState.IDLE},
    OrchestrationState.FAILED: set(),
}
