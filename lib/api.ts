const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const WS_URL = API_URL.replace(/^http/, "ws");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Health ---

export function getHealth() {
  return request<{ status: string }>("/health");
}

// --- Questions ---

export interface QuestionExample {
  input: string;
  output: string;
  explanation?: string | null;
}

export interface Question {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  acceptance_rate: number | null;
  related_topics: string[];
  url: string | null;
  examples: QuestionExample[];
  constraints: string[];
}

export interface QuestionListResponse {
  questions: Question[];
  total: number;
  skip: number;
  limit: number;
}

export function listQuestions(params?: {
  difficulty?: string;
  skip?: number;
  limit?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.difficulty) qs.set("difficulty", params.difficulty);
  if (params?.skip !== undefined) qs.set("skip", String(params.skip));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  const suffix = qs.toString() ? `?${qs}` : "";
  return request<QuestionListResponse>(`/questions${suffix}`);
}

export function getRandomQuestion(difficulty?: string) {
  const qs = difficulty ? `?difficulty=${encodeURIComponent(difficulty)}` : "";
  return request<Question>(`/questions/random${qs}`);
}

export function getQuestion(id: number) {
  return request<Question>(`/questions/${id}`);
}

// --- Sessions ---

export interface Session {
  session_id: string;
  round_type: string;
  difficulty: string | null;
  title: string | null;
  status: string;
  question_id: number | null;
  created_at: string;
  updated_at: string;
  duration_minutes: number | null;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

export function createSession(body: {
  round_type: string;
  difficulty?: string;
  title?: string;
}) {
  return request<Session>("/sessions/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getSession(sessionId: string) {
  return request<Session>(`/sessions/${sessionId}`);
}

export function listSessions() {
  return request<SessionListResponse>("/sessions/");
}

export function startSession(sessionId: string) {
  return request<Session>(`/sessions/${sessionId}/start`, { method: "POST" });
}

export function endSession(sessionId: string) {
  return request<Session>(`/sessions/${sessionId}/end`, { method: "POST" });
}

// --- Code Events ---

export interface CodeEvent {
  event_id: string;
  session_id: string;
  language: string;
  content: string;
  file_path: string;
  created_at: string;
}

export function submitCodeEvent(body: {
  session_id: string;
  language: string;
  content: string;
  file_path?: string;
}) {
  return request<CodeEvent>("/code-events/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listCodeEvents(sessionId: string) {
  return request<{ events: CodeEvent[]; total: number }>(
    `/code-events/${sessionId}`
  );
}

// --- WebSocket ---

export function connectWebSocket(
  sessionId: string,
  handlers: {
    onMessage?: (data: Record<string, unknown>) => void;
    onOpen?: () => void;
    onClose?: () => void;
    onError?: (e: Event) => void;
  }
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/${sessionId}`);

  ws.onopen = () => handlers.onOpen?.();
  ws.onclose = () => handlers.onClose?.();
  ws.onerror = (e) => handlers.onError?.(e);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onMessage?.(data);
    } catch {
      // ignore non-JSON messages
    }
  };

  return ws;
}

export function sendTranscript(
  ws: WebSocket,
  content: string,
  roundType: string = "coding"
) {
  ws.send(
    JSON.stringify({
      type: "transcript.user",
      content,
      round_type: roundType,
    })
  );
}

export function sendTranscriptPartial(
  ws: WebSocket,
  body: {
    text_delta: string;
    speaker?: "user" | "interviewer";
    confidence?: number;
    start_ms?: number;
    end_ms?: number;
  }
) {
  ws.send(
    JSON.stringify({
      type: "transcript.partial",
      speaker: body.speaker ?? "user",
      text_delta: body.text_delta,
      confidence: body.confidence,
      start_ms: body.start_ms,
      end_ms: body.end_ms,
    })
  );
}

export function sendTranscriptFinal(
  ws: WebSocket,
  body: {
    text: string;
    speaker?: "user" | "interviewer";
    confidence?: number;
    start_ms?: number;
    end_ms?: number;
    pause_before_ms?: number;
    pause_after_ms?: number;
  }
) {
  ws.send(
    JSON.stringify({
      type: "transcript.final",
      speaker: body.speaker ?? "user",
      text: body.text,
      confidence: body.confidence,
      start_ms: body.start_ms,
      end_ms: body.end_ms,
      pause_before_ms: body.pause_before_ms,
      pause_after_ms: body.pause_after_ms,
    })
  );
}

export function sendCodeChanged(
  ws: WebSocket,
  body: {
    language: string;
    content_snapshot: string;
    file_path?: string;
    content_hash?: string;
    diff_summary?: { additions?: number; deletions?: number };
  }
) {
  const computedHash =
    body.content_hash ||
    (typeof window !== "undefined" && "btoa" in window
      ? window.btoa(unescape(encodeURIComponent(body.content_snapshot))).slice(0, 32)
      : String(body.content_snapshot.length));

  ws.send(
    JSON.stringify({
      type: "code.changed",
      language: body.language,
      file_path: body.file_path ?? "main",
      content_snapshot: body.content_snapshot,
      content_hash: computedHash,
      diff_summary: body.diff_summary,
    })
  );
}

export function sendCodeRunCompleted(
  ws: WebSocket,
  body: {
    stdout?: string;
    stderr?: string;
    exit_code: number;
    runtime_ms?: number;
    tests_passed?: number;
    tests_failed?: number;
  }
) {
  ws.send(
    JSON.stringify({
      type: "code.run_completed",
      stdout: body.stdout,
      stderr: body.stderr,
      exit_code: body.exit_code,
      runtime_ms: body.runtime_ms,
      tests_passed: body.tests_passed,
      tests_failed: body.tests_failed,
    })
  );
}

// --- Audio WebSocket ---

export function connectAudioWebSocket(
  sessionId: string,
  mode: "langgraph" | "convai" = "langgraph",
  handlers: {
    onMessage?: (data: Record<string, unknown>) => void;
    onOpen?: () => void;
    onClose?: () => void;
    onError?: (e: Event) => void;
  }
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/audio/${sessionId}`);

  ws.onopen = () => {
    ws.send(JSON.stringify({ mode }));
    handlers.onOpen?.();
  };
  ws.onclose = () => handlers.onClose?.();
  ws.onerror = (e) => handlers.onError?.(e);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onMessage?.(data);
    } catch {
      // ignore non-JSON messages
    }
  };

  return ws;
}

export function sendAudioChunk(ws: WebSocket, audioBase64: string) {
  ws.send(
    JSON.stringify({
      type: "audio.chunk",
      audio_base64: audioBase64,
    })
  );
}

export function sendAudioControl(
  ws: WebSocket,
  action: "mute" | "unmute" | "stop" | "commit"
) {
  ws.send(
    JSON.stringify({
      type: "audio.control",
      action,
    })
  );
}

// --- ConvAI Agent ---

export interface ConvAIAgentResponse {
  agent_id: string;
  name: string;
}

export function createConvAIAgent() {
  return request<ConvAIAgentResponse>("/convai/agent", {
    method: "POST",
  });
}
