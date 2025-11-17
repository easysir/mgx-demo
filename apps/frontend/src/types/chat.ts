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
  id: string; // 消息唯一标识
  session_id: string; // 所属会话 id
  sender: SenderRole; // 发送方（user/agent/status 等）
  content: string; // 文本内容
  timestamp: string; // ISO 时间戳
  agent?: AgentRole | null; // 若 sender 为 agent，指出具体角色
}

export interface ChatTurn {
  user: Message;
  responses: Message[];
}

export interface StreamEvent {
  type: 'token' | 'status' | 'error' | 'file_change' | 'message' | 'tool_call'; // 推送事件类别
  sender?: SenderRole; // 消息来源（user/agent/status）
  agent?: AgentRole | null; // 具体哪位 agent 触发
  content?: string; // 文本内容或状态描述
  message_id?: string; // 该事件所属消息的唯一 id
  final?: boolean; // 是否为该消息的最终片段
  session_id?: string; // 所属会话 id
  timestamp?: string; // 事件时间
  sequence?: number; // 流式顺序号，便于排序
  paths?: string[]; // 受影响的文件路径（文件变更事件）
  tool?: string; // 工具调用名称
  invoker?: string; // 谁触发了工具调用
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

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number;
  children?: FileNode[];
}

export interface FileTreeResponse {
  root: string;
  entries: FileNode[];
}

export interface FileContentResponse {
  name: string;
  path: string;
  size: number;
  modified_at: number;
  content: string;
}

export interface SandboxPreviewTarget {
  container_port: number;
  host_port: number;
  url: string;
}

export interface SandboxPreviewResponse {
  session_id: string;
  available: boolean;
  previews: SandboxPreviewTarget[];
}
