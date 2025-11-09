'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { login, error, loading } = useAuth();
  const [email, setEmail] = useState('demo@mgx.dev');
  const [password, setPassword] = useState('mgx-demo');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      await login(email, password);
      router.push('/');
    } catch {
      // 错误信息由 useAuth 管理
    }
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <button className="ghost login-back" type="button" onClick={() => router.push('/')}>
          ← 返回首页
        </button>
        <h1>登录 MGX</h1>
        <form onSubmit={handleSubmit}>
          <label>
            邮箱
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? '登录中...' : '登录'}
          </button>
          {error && <p className="workspace__error">{error}</p>}
        </form>
      </section>
    </main>
  );
}
