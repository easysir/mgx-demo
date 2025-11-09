export type AgentRole = 'Mike' | 'Emma' | 'Bob' | 'Alex' | 'David' | 'Iris';

export type SenderRole = 'user' | 'mike' | 'agent' | 'status';

export interface Session {
  id: string;
  title: string;
  created_at: string;
  messages?: Message[];
  owner_id: string;
}

export interface Message {
  id: string;
  session_id: string;
  sender: SenderRole;
  content: string;
  timestamp: string;
  agent?: AgentRole | null;
}

export interface ChatTurn {
  user: Message;
  responses: Message[];
}

export interface StreamEvent {
  type: 'token' | 'status' | 'error';
  sender: SenderRole;
  agent?: AgentRole | null;
  content: string;
  message_id: string;
  final: boolean;
  session_id?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  credits: number;
  plan: string;
}
