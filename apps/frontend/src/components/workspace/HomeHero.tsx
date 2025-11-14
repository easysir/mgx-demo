'use client';

import { FormEvent } from 'react';

import type { Session } from '@/types/chat';

import { SessionListPanel } from './SessionListPanel';

interface HomeHeroProps {
  showHistory: boolean;
  sessions: Session[];
  isLoadingSessions: boolean;
  isSending: boolean;
  homeDraft: string;
  onHomeDraftChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onOpenSession: (id: string) => Promise<void>;
  onDeleteSession: (id: string) => Promise<void>;
}

export function HomeHero({
  showHistory,
  sessions,
  isLoadingSessions,
  isSending,
  homeDraft,
  onHomeDraftChange,
  onSubmit,
  onOpenSession,
  onDeleteSession
}: HomeHeroProps) {
  return (
    <div className="workspace__home-layout">
      {showHistory && (
        <SessionListPanel
          sessions={sessions}
          isLoading={isLoadingSessions}
          isBusy={isSending}
          onOpen={onOpenSession}
          onDelete={onDeleteSession}
        />
      )}
      <section className="workspace__home">
        <div className="workspace__home-card">
          <form className="workspace__home-form" onSubmit={onSubmit}>
            <div className="workspace__home-input">
              <textarea
                rows={6}
                placeholder="例如：搭建一个带深色导航和作品集的个人网站..."
                value={homeDraft}
                onChange={(event) => onHomeDraftChange(event.target.value)}
                disabled={isSending}
              />
              <button type="submit" className="workspace__home-submit" disabled={isSending}>
                {isSending ? '生成会话中...' : '确认'}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
