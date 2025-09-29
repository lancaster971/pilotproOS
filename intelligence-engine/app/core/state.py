"""
State Management System
Immutable state with versioning and event sourcing
PRODUCTION-READY - NO MOCK DATA
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import hashlib
import json
from dataclasses import dataclass, field
import asyncio
import asyncpg

from app.database import get_db_connection

import logging
logger = logging.getLogger(__name__)


class StateStatus(str, Enum):
    """State lifecycle status"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StateEvent(BaseModel):
    """Immutable event for state changes"""
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(description="Unique event identifier")
    event_type: str = Field(description="Type of state change")
    timestamp: datetime = Field(default_factory=datetime.now)
    actor: str = Field(description="Who/what triggered the event")
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "data": self.data,
            "metadata": self.metadata
        }


class AgentState(BaseModel):
    """
    Immutable agent state with versioning
    Each modification creates a new version
    """
    model_config = ConfigDict(frozen=True)

    # Core state
    state_id: str = Field(description="Unique state identifier")
    version: int = Field(default=1, description="State version number")
    status: StateStatus = Field(default=StateStatus.CREATED)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Agent context
    agent_name: str = Field(description="Name of the agent")
    session_id: str = Field(description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")

    # State data
    data: Dict[str, Any] = Field(default_factory=dict, description="State payload")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Event sourcing
    events: List[StateEvent] = Field(default_factory=list, description="Event history")
    parent_state_id: Optional[str] = Field(default=None, description="Previous state ID")

    def evolve(self, **changes) -> "AgentState":
        """
        Create new state version with changes
        Original state remains immutable
        """
        # Get current data as dict
        current_data = self.model_dump()

        # Update version and timestamps
        current_data["version"] = self.version + 1
        current_data["updated_at"] = datetime.now()
        current_data["parent_state_id"] = self.state_id

        # Generate new state ID
        current_data["state_id"] = self._generate_state_id(
            self.agent_name,
            self.session_id,
            current_data["version"]
        )

        # Apply changes
        for key, value in changes.items():
            if key in current_data and key not in ["state_id", "version", "created_at"]:
                current_data[key] = value

        # Create event for this evolution
        event = StateEvent(
            event_id=hashlib.md5(
                f"{self.state_id}-{current_data['version']}".encode()
            ).hexdigest(),
            event_type="state_evolution",
            actor=changes.get("actor", "system"),
            data=changes,
            metadata={"previous_version": self.version}
        )

        # Add event to history
        current_data["events"] = list(self.events) + [event]

        # Return new immutable state
        return AgentState(**current_data)

    def add_event(self, event: StateEvent) -> "AgentState":
        """Add event and return new state"""
        return self.evolve(events=list(self.events) + [event])

    def get_hash(self) -> str:
        """Get hash of current state for integrity"""
        state_str = json.dumps(self.model_dump(), sort_keys=True, default=str)
        return hashlib.sha256(state_str.encode()).hexdigest()

    @staticmethod
    def _generate_state_id(agent_name: str, session_id: str, version: int) -> str:
        """Generate unique state ID"""
        return hashlib.md5(
            f"{agent_name}-{session_id}-{version}-{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]


class StateManager:
    """
    Manages state lifecycle with persistence and recovery
    """

    def __init__(self, enable_persistence: bool = True):
        self.enable_persistence = enable_persistence
        self.states: Dict[str, AgentState] = {}
        self.state_history: Dict[str, List[AgentState]] = {}
        self._lock = asyncio.Lock()

    async def create_state(
        self,
        agent_name: str,
        session_id: str,
        initial_data: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> AgentState:
        """Create new agent state"""
        async with self._lock:
            state = AgentState(
                state_id=AgentState._generate_state_id(agent_name, session_id, 1),
                agent_name=agent_name,
                session_id=session_id,
                user_id=user_id,
                data=initial_data or {},
                status=StateStatus.CREATED
            )

            # Store in memory
            self.states[state.state_id] = state

            # Initialize history
            if session_id not in self.state_history:
                self.state_history[session_id] = []
            self.state_history[session_id].append(state)

            # Persist if enabled
            if self.enable_persistence:
                await self._persist_state(state)

            logger.info(f"Created state {state.state_id} for {agent_name}")
            return state

    async def update_state(
        self,
        state_id: str,
        changes: Dict[str, Any],
        actor: str = "system"
    ) -> AgentState:
        """Update state (creates new version)"""
        async with self._lock:
            if state_id not in self.states:
                raise ValueError(f"State {state_id} not found")

            old_state = self.states[state_id]

            # Add actor to changes
            changes["actor"] = actor

            # Evolve to new state
            new_state = old_state.evolve(**changes)

            # Update storage
            self.states[new_state.state_id] = new_state

            # Add to history
            session_id = new_state.session_id
            if session_id in self.state_history:
                self.state_history[session_id].append(new_state)

            # Persist if enabled
            if self.enable_persistence:
                await self._persist_state(new_state)

            logger.info(f"Updated state {state_id} -> {new_state.state_id} (v{new_state.version})")
            return new_state

    async def get_state(self, state_id: str) -> Optional[AgentState]:
        """Get state by ID"""
        async with self._lock:
            return self.states.get(state_id)

    async def get_session_history(self, session_id: str) -> List[AgentState]:
        """Get all states for a session"""
        async with self._lock:
            return self.state_history.get(session_id, [])

    async def rollback_state(self, state_id: str) -> Optional[AgentState]:
        """Rollback to previous state version"""
        async with self._lock:
            if state_id not in self.states:
                return None

            current_state = self.states[state_id]

            if not current_state.parent_state_id:
                logger.warning(f"Cannot rollback {state_id} - no parent state")
                return None

            # Find parent state
            parent_state = None
            for state in self.states.values():
                if state.state_id == current_state.parent_state_id:
                    parent_state = state
                    break

            if not parent_state:
                logger.error(f"Parent state {current_state.parent_state_id} not found")
                return None

            # Create rollback event
            rollback_event = StateEvent(
                event_id=hashlib.md5(f"rollback-{state_id}".encode()).hexdigest(),
                event_type="rollback",
                actor="system",
                data={"from_version": current_state.version, "to_version": parent_state.version},
                metadata={"reason": "manual_rollback"}
            )

            # Create rolled back state
            rolled_back = parent_state.add_event(rollback_event).evolve(
                status=StateStatus.ROLLED_BACK
            )

            # Update storage
            self.states[rolled_back.state_id] = rolled_back

            logger.info(f"Rolled back {state_id} to {rolled_back.state_id}")
            return rolled_back

    async def _persist_state(self, state: AgentState):
        """Persist state to database"""
        try:
            conn = await get_db_connection()

            # Store in intelligence.agent_states table
            await conn.execute("""
                INSERT INTO intelligence.agent_states
                (state_id, version, agent_name, session_id, user_id,
                 status, data, context, metadata, events, parent_state_id,
                 state_hash, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (state_id) DO NOTHING
            """,
                state.state_id,
                state.version,
                state.agent_name,
                state.session_id,
                state.user_id,
                state.status.value,
                json.dumps(state.data),
                json.dumps(state.context),
                json.dumps(state.metadata),
                json.dumps([e.to_dict() for e in state.events]),
                state.parent_state_id,
                state.get_hash(),
                state.created_at,
                state.updated_at
            )

            await conn.close()
            logger.debug(f"Persisted state {state.state_id} to database")

        except asyncpg.PostgresError as e:
            # If table doesn't exist, create it
            if "relation" in str(e) and "does not exist" in str(e):
                await self._create_state_table()
                # Retry persistence
                await self._persist_state(state)
            else:
                logger.error(f"Failed to persist state: {e}")

    async def _create_state_table(self):
        """Create state storage table if not exists"""
        try:
            conn = await get_db_connection()

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS intelligence.agent_states (
                    state_id VARCHAR(32) PRIMARY KEY,
                    version INTEGER NOT NULL,
                    agent_name VARCHAR(100) NOT NULL,
                    session_id VARCHAR(100) NOT NULL,
                    user_id VARCHAR(100),
                    status VARCHAR(20) NOT NULL,
                    data JSONB,
                    context JSONB,
                    metadata JSONB,
                    events JSONB,
                    parent_state_id VARCHAR(32),
                    state_hash VARCHAR(64) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,

                    CONSTRAINT fk_parent_state
                        FOREIGN KEY (parent_state_id)
                        REFERENCES intelligence.agent_states(state_id)
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_states_session
                ON intelligence.agent_states(session_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_states_agent
                ON intelligence.agent_states(agent_name)
            """)

            await conn.close()
            logger.info("Created agent_states table")

        except Exception as e:
            logger.error(f"Failed to create state table: {e}")

    async def recover_session(self, session_id: str) -> List[AgentState]:
        """Recover session states from database"""
        try:
            conn = await get_db_connection()

            rows = await conn.fetch("""
                SELECT * FROM intelligence.agent_states
                WHERE session_id = $1
                ORDER BY version ASC
            """, session_id)

            await conn.close()

            states = []
            for row in rows:
                # Reconstruct events
                events = []
                if row['events']:
                    for event_data in row['events']:
                        events.append(StateEvent(**event_data))

                # Reconstruct state
                state = AgentState(
                    state_id=row['state_id'],
                    version=row['version'],
                    status=StateStatus(row['status']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    agent_name=row['agent_name'],
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    data=row['data'] or {},
                    context=row['context'] or {},
                    metadata=row['metadata'] or {},
                    events=events,
                    parent_state_id=row['parent_state_id']
                )

                states.append(state)

                # Restore to memory
                self.states[state.state_id] = state

            # Restore history
            self.state_history[session_id] = states

            logger.info(f"Recovered {len(states)} states for session {session_id}")
            return states

        except Exception as e:
            logger.error(f"Failed to recover session: {e}")
            return []


# Singleton instance
state_manager = StateManager(enable_persistence=True)

__all__ = [
    'AgentState',
    'StateEvent',
    'StateStatus',
    'StateManager',
    'state_manager'
]