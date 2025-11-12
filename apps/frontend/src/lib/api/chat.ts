import {
  ChatTurn,
  Message,
  Session,
  TokenResponse,
  UserProfile,
  FileTreeResponse,
  FileContentResponse,
  SandboxPreviewResponse
} from '@/types/chat';

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail ?? response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

const authHeaders = (token: string, headers: Record<string, string> = {}) => ({
  ...headers,
  Authorization: `Bearer ${token}`
});

export async function createSession(token: string, title?: string): Promise<Session> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(title ? { title } : {})
  });
  return handleResponse<Session>(response);
}

export async function fetchMessages(token: string, sessionId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
    headers: authHeaders(token)
  });
  return handleResponse<Message[]>(response);
}

export async function listSessions(token: string): Promise<Session[]> {
  const response = await fetch(`${API_BASE}/sessions`, {
    headers: authHeaders(token)
  });
  return handleResponse<Session[]>(response);
}

export async function sendMessage(token: string, sessionId: string, content: string): Promise<ChatTurn> {
  const response = await fetch(`${API_BASE}/chat/messages`, {
    method: 'POST',
    headers: authHeaders(token, { 'Content-Type': 'application/json' }),
    body: JSON.stringify({ session_id: sessionId, content })
  });
  return handleResponse<ChatTurn>(response);
}

export async function fetchFileTree(
  token: string,
  sessionId: string,
  params: { root?: string; depth?: number; includeHidden?: boolean } = {}
): Promise<FileTreeResponse> {
  const query = new URLSearchParams();
  if (params.root) query.set('root', params.root);
  if (params.depth) query.set('depth', String(params.depth));
  if (params.includeHidden) query.set('include_hidden', 'true');
  const url = `${API_BASE}/files/${sessionId}/tree${query.size ? `?${query.toString()}` : ''}`;
  const response = await fetch(url, { headers: authHeaders(token) });
  return handleResponse<FileTreeResponse>(response);
}

export async function fetchFileContent(token: string, sessionId: string, path: string): Promise<FileContentResponse> {
  const url = `${API_BASE}/files/${sessionId}?${new URLSearchParams({ path }).toString()}`;
  const response = await fetch(url, { headers: authHeaders(token) });
  return handleResponse<FileContentResponse>(response);
}

export async function fetchSandboxPreview(token: string, sessionId: string): Promise<SandboxPreviewResponse> {
  const response = await fetch(`${API_BASE}/sandbox/preview/${sessionId}`, {
    headers: authHeaders(token)
  });
  return handleResponse<SandboxPreviewResponse>(response);
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return handleResponse<TokenResponse>(response);
}

export async function fetchProfile(token: string): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/auth/me?token=${encodeURIComponent(token)}`);
  return handleResponse<UserProfile>(response);
}

export async function deleteSession(token: string, sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: authHeaders(token)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail ?? response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
}
