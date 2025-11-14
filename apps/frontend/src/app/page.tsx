'use client';

import Link from 'next/link';
import { useState } from 'react';

import { HomeHero } from '@/components/workspace/HomeHero';
import { WorkspaceShell } from '@/components/workspace/WorkspaceShell';
import { useWorkspace } from '@/hooks/useWorkspace';

export default function Home() {
  const {
    user,
    logout,
    sessionId,
    sessions,
    messages,
    streamingMessages,
    homeDraft,
    setHomeDraft,
    isSending,
    isLoadingSessions,
    error,
    fileVersion,
    isHomeView,
    handleSend,
    handleOpenSession,
    handleDeleteSession,
    handleHomeSubmit,
    handleBackHome
  } = useWorkspace();
  const [activeRightTab, setActiveRightTab] = useState<'editor' | 'preview'>('editor');

  return (
    <main className={`workspace ${isHomeView ? 'workspace--home' : 'workspace--chat'}`}>
      <header className="workspace__nav">
        <div className="workspace__nav-left">
          <button className="workspace__logo" onClick={handleBackHome}>
            MGX
          </button>
        </div>

        <div className="workspace__nav-right">
          {user ? (
            <div className="workspace__user">
              <div>
                <span className="">{user.name}</span>
                <small>
                  {user.plan} · {user.credits} credits
                </small>
              </div>
              <div className="ghost" onClick={logout}>
                登出
              </div>
            </div>
          ) : (
            <Link className="ghost" href="/login">
              登录
            </Link>
          )}
        </div>
      </header>

      {isHomeView ? (
        <HomeHero
          showHistory={Boolean(user)}
          sessions={sessions}
          isLoadingSessions={isLoadingSessions}
          isSending={isSending}
          homeDraft={homeDraft}
          onHomeDraftChange={setHomeDraft}
          onSubmit={handleHomeSubmit}
          onOpenSession={handleOpenSession}
          onDeleteSession={handleDeleteSession}
        />
      ) : (
        <WorkspaceShell
          sessionId={sessionId}
          messages={messages}
          streamingMessages={streamingMessages}
          isSending={isSending}
          error={error}
          onSend={handleSend}
          activeTab={activeRightTab}
          onTabChange={setActiveRightTab}
          fileVersion={fileVersion}
        />
      )}
    </main>
  );
}
