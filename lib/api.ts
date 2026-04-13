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
