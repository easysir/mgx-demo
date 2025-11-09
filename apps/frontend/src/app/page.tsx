export default function Home() {
  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem'
      }}
    >
      <h1>MGX Workspace</h1>
      <p>Monorepo 初始化完成，后续将在此实现 Chat Workspace / Editor / Preview 体验。</p>
    </main>
  );
}

