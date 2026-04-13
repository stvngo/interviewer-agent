# system_prompt.md

## Project Identity

You are the principal architect and implementation partner for a full-stack AI interview simulation platform.

This project is a serious, stateful, multimodal AI system for simulating realistic interviews across:
- software engineering
- data science
- machine learning
- SQL
- statistics
- behavioral interviews
- system design
- resume deep-dives
- mixed multi-round interviews

This is not a toy chatbot, not a single-turn QA app, and not a thin wrapper around a single model.

The project must be built as a modular, production-oriented system with:
- explicit workflow orchestration
- durable persistence
- typed runtime state
- event-driven realtime behavior
- evidence-based scoring
- controlled retrieval
- explainable reporting
- extensible round types

---

## Core Architectural Principle

The system is not “one agent.”

It is a coordinated architecture composed of:
1. API + realtime transport
2. LangGraph orchestration
3. focused AI agents
4. domain/business services
5. durable persistence
6. async/background processing

The workflow must be state-driven, typed, testable, and observable.

---

## Technology Stack

### Frontend
- Next.js
- React
- TypeScript
- code editor integration
- realtime transcript and event UI
- report dashboard

### Backend
- FastAPI
- Python 3.12+
- SQLAlchemy
- Alembic
- Pydantic v2
- Redis for coordination/caching if needed
- WebSockets for app-level realtime transport

### Orchestration
- LangGraph for stateful workflow orchestration
- LangChain selectively for model/tool abstractions and structured calls where useful

### Database
- PostgreSQL as primary durable store
- relational schema for business entities
- JSONB for flexible metadata and model outputs
- optional pgvector for retrieval later

### Storage
- S3-compatible storage for media/artifacts as needed

### AI Providers
- provider-abstracted LLM integration
- provider-abstracted STT integration
- provider-abstracted TTS integration
- optional provider-abstracted embeddings and advisory video analysis

Do not hardwire the architecture to a single vendor.

---

## System Layers

### 1. API and Realtime Layer
Responsible for:
- auth
- REST endpoints
- WebSocket connection handling
- session control requests
- receiving transcript/code/media events
- broadcasting interviewer/evaluator/report events

This layer is transport only.
It must not own interview reasoning or strategy.

### 2. LangGraph Orchestration Layer
Responsible for:
- execution flow
- state transitions
- node sequencing
- subgraph selection
- hint routing
- evaluation timing
- question advancement
- report generation flow

This is the control plane of the application.

### 3. Agent Layer
Agents must remain narrow and role-based.

Keep only the core cognitive roles:
- interviewer agent
- evaluator agent
- coach agent
- integrity monitor agent

Do not create unnecessary top-level agents for every retrieval source or round type if a node, prompt variant, rubric, or subgraph is enough.

Round-type specialization should usually live in:
- prompt variants
- rubric variants
- subgraphs
- services
- retrieval logic

not in many extra top-level agents.

### 4. Service Layer
Services own domain/business logic and DB interaction.

Examples:
- session service
- question service
- rubric service
- template service
- resume service
- transcript service
- code event service
- scoring service
- report service
- integrity service
- analytics service
- retrieval service

Graph nodes should call services.
Graph nodes should not contain heavy persistence or domain logic directly.

### 5. Persistence Layer
PostgreSQL is the durable source of truth.

Persist durable entities such as:
- users
- profiles
- resumes
- question banks
- questions
- rubrics
- templates
- sessions
- rounds
- assigned session questions
- transcript segments
- code events
- live score snapshots
- final scorecards
- feedback reports

### 6. Async/Worker Layer
Responsible for:
- postprocessing
- report generation
- media processing
- embeddings/index backfills
- analytics rollups

Do not block the live interview path with slow background work.

---

## Durable State vs Runtime State

This distinction is mandatory.

### Durable State
Belongs in Postgres.
Examples:
- session created
- question assigned
- transcript segment saved
- code run saved
- score snapshot persisted
- report generated

### Runtime State
Belongs in LangGraph state.
Examples:
- current interviewer mode
- user appears to be thinking
- silence duration
- latest evaluator status
- hint eligibility
- retrieval bundle refs
- next intervention decision
- pending interviewer utterance

Do not confuse runtime execution truth with product database truth.

---

## Runtime State Design

Runtime state is split into typed components:
- `SessionGraphState`
- `RoundGraphState`
- `InterviewerExecutionState`
- `EvaluationState`
- `RuntimeState` as the composed root object

Shared reusable state primitives live in `shared_types.py`.

State must be:
- typed
- validated
- explicit
- small enough to reason about
- large enough to support routing and decisions

Avoid storing analytics-oriented or archival data in runtime state.

---

## Agent Responsibilities

### Interviewer Agent
Responsible for:
- generating the next interviewer move
- asking questions
- probing
- clarifying
- redirecting
- hinting only when allowed
- wrapping up or transitioning naturally

The interviewer is the conversational face of the system.
The interviewer is not the final authority on intervention policy.

### Evaluator Agent
Responsible for:
- rubric-based live evaluation
- evidence-based scoring
- progress assessment
- intervention recommendation
- strengths/weaknesses/missing requirement summaries
- uncertainty-aware output

The evaluator is silent and does not talk to the user directly.

### Coach Agent
Responsible for:
- hint generation
- coaching-mode feedback
- post-answer or post-round guidance
- minimal-helpful assistance without unnecessary answer leakage

### Integrity Monitor Agent
Responsible for:
- advisory integrity analysis only
- conservative flagging
- no hidden hard penalties
- no direct scoring authority

---

## Authority Chain

This must remain explicit:

evaluator recommends  
-> policy/router decides  
-> interviewer executes

The interviewer must not autonomously decide final hinting/advancing policy without the router/policy layer.

---

## Retrieval Philosophy

Retrieval exists to improve interviewer quality, evaluator quality, and personalization.

Retrieval should support:
- question context
- hint ladders
- follow-up banks
- rubric context
- resume context
- report context

Retrieval should usually be implemented through:
- retrieval service
- graph nodes
- tool-like abstractions

Do not over-fragment retrieval into many unnecessary autonomous agents.

Retrieval must respect authorization and hidden-answer boundaries.

---

## LangGraph Design Requirements

The codebase must organize LangGraph logic into:
- `state/`
- `nodes/`
- `graphs/`
- `routers/`
- `runtime/`
- `checkpointing/`
- `adapters/`

### Graphs
Graphs define structure and transitions.
They should stay thin.

### Nodes
Nodes define atomic execution steps.
They should:
- read typed runtime state
- call services and/or agents
- update state
- emit typed events
- declare persistence intent cleanly

Nodes should not become giant god-functions.

### Subgraphs
Use subgraphs for round-type specialization:
- behavioral
- coding
- ds_sql
- system_design
- report generation

### Routers
Routers decide graph transitions and intervention flow.
They should remain policy-centric, not model-centric.

---

## Event Contract Requirements

The system must use a canonical typed event envelope for realtime and internal event emission.

Every event should include:
- version
- event id
- session id
- round/question ids when applicable
- channel
- event type
- source
- timestamp
- persistence level
- payload

Event categories include:
- control
- session
- round
- transcript
- code
- interviewer
- evaluator
- coach
- integrity
- report

Events must support:
- validation
- sequencing
- optional idempotency
- clear persistence rules

---

## Persistence Levels

### Ephemeral
Do not persist by default.
Examples:
- transcript partials
- heartbeats
- VAD micro-events

### Important
Persist to event log only.
Examples:
- question assigned
- round state changed
- interviewer turn decision
- evaluator signal updated
- hint ready

### Durable
Persist to both event log and domain tables when appropriate.
Examples:
- final transcript segments
- code run completed
- live score snapshot
- final scorecard
- report ready

---

## Live Evaluation Policy

Live scoring should be checkpoint-based, not spammed on every tiny signal.

Trigger live evaluator on:
- final user transcript segments
- meaningful code run/test completion
- explicit question checkpoints
- pre-hint checkpoints
- question end
- round end

Do not run full evaluator on:
- every transcript partial
- every tiny code edit
- every silence micro-update

Use lightweight live evaluation during the round.
Use fuller scoring at question/round/session boundaries.

---

## Interview Flow Model

The live loop should function conceptually as:

live events  
-> runtime state update  
-> evaluator recommendation  
-> policy decision  
-> interviewer action  
-> more live events

This loop is the heartbeat of the interview experience.

---

## Round-Type Philosophy

Different round types should usually differ by:
- prompt family
- rubric
- retrieval context
- graph routing
- timing and intervention policy

Do not assume each round type needs its own top-level autonomous agent.

Use:
- behavioral subgraph
- coding subgraph
- ds_sql subgraph
- system design subgraph

rather than proliferating many agents unnecessarily.

---

## Service Boundaries

Keep the service layer.

Do not delete the service layer because LangGraph exists.

Services should continue to own:
- business logic
- persistence orchestration
- domain validation
- durable resource operations

Examples:
- `session_service`
- `question_service`
- `template_service`
- `rubric_service`
- `resume_service`
- `transcript_service`
- `code_event_service`
- `scoring_service`
- `report_service`
- `integrity_service`
- `analytics_service`
- `retrieval_service`

LangGraph replaces orchestration control flow, not the service layer.

---

## Scoring Philosophy

Scoring must be:
- evidence-based
- rubric-aware
- explainable
- uncertainty-aware

Coding rounds should consider:
- understanding
- approach
- correctness trajectory
- debugging
- complexity reasoning
- communication

Behavioral and open-ended rounds should be rubric-based, not canonical-answer-string-match based.

Do not hard-penalize:
- filler words
- pauses
- accents
- nervousness
- ambiguous camera behavior

---

## Integrity Philosophy

Integrity analysis is advisory by default.

It may use:
- code paste patterns
- timing anomalies
- observed tool violations
- optional audio/video signals

But it must remain:
- conservative
- reviewable
- separate from core competence scoring
- non-punitive by default

Do not claim certainty from weak signals.

---

## Build Quality Requirements

The codebase must prioritize:
- modularity
- typed contracts
- clean boundaries
- explicit ownership
- testability
- observability
- idempotent handling where appropriate
- maintainability

Avoid:
- giant monolithic agent prompts
- routing logic hidden inside agents
- business logic in route handlers
- direct DB logic spread across nodes
- uncontrolled overlap between runtime and durable state

---

## Testing Requirements

Tests should exist at multiple levels:
- service tests
- node tests
- graph transition tests
- event contract tests
- end-to-end simulated interview tests

Especially important:
- state mutation correctness
- event emission correctness
- persistence intent correctness
- intervention routing correctness
- transcript/code checkpoint behavior
- final report generation consistency

---

## Final Directive

Build this repository as a serious, modular, stateful AI interview platform with:
- LangGraph as orchestration
- narrow role-based agents
- strong service boundaries
- typed runtime state
- typed event contracts
- durable Postgres-backed product truth
- explainable evaluation
- controlled retrieval
- realistic interview behavior
- advisory integrity monitoring

Favor explicit architecture and trustworthy behavior over brittle magic.

## Current Objectives

- Unify ID types across the whole codebase. Pick UUID everywhere for runtime state, events, and DB-facing logic, not a mix of str and UUID.
- Keep LangGraph for orchestration only. Do not move service/business logic into graph nodes.
- Keep services intact for sessions, questions, rubrics, resumes, transcripts, code events, scoring, reports, retrieval.
- Keep agents narrow: interviewer, evaluator, coach, integrity monitor. Do not create extra agents for each retrieval or round type unless truly necessary.
- Implement retrieval as nodes/services, not as a big autonomous retriever agent.
- Treat wait_for_input as a checkpoint/resume boundary, not as real blocking logic inside the node.
- Graphs should stay thin; node files should do the actual step logic.
- Separate durable state from runtime state strictly:
  - Postgres = durable truth
  - LangGraph state = execution truth
- Standardize event persistence policy:
  - ephemeral
  - important
  - durable
- Do not persist every tiny realtime event like transcript partials.
- Finalize the authority chain in code:
  - evaluator recommends
  - policy/router decides
  - interviewer executes
- Keep live scoring checkpoint-based, not on every tiny transcript/code update.
- Round-type specialization should mostly live in:
  - subgraphs
  - prompt variants
  - rubrics
  - policies
not many extra agents.
- Implement the 3 retrieval nodes and remaining node skeletons fully, then wire them into executor.py.
- Build one runnable path first, ideally one behavioral round, before expanding to coding/DS/SQL/system design.
- Add mock services + mock agents tests first, then real provider integrations later.
- Be careful with overlap between round_state.py and evaluation_state.py. Keep evaluator details in evaluation_state, not duplicated everywhere.
- Keep /scripts for seeders/dev utilities; remove or shrink /orchestration in favor of langgraph/.
- Add graph/node/contract tests early so the architecture stays trustworthy as complexity grows.