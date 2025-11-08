export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">MGX MVP</h1>
        <p className="text-xl mb-8">AI-Powered Development Platform</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">6-Person Team</h2>
            <p>Mike, Emma, Bob, Alex, David, Iris</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">Real-time Chat</h2>
            <p>WebSocket-based streaming</p>
          </div>
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-2">Live Preview</h2>
            <p>See your app in real-time</p>
          </div>
        </div>
      </div>
    </main>
  );
}