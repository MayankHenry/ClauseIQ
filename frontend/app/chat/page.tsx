import ChatInterface from "@/components/ChatInterface";

export default function ChatPage() {
  return (
    <div>
      <p className="mb-1 font-mono text-xs uppercase tracking-widest text-muted">
        Examination
      </p>
      <h1 className="mb-1 font-display text-xl font-semibold text-ink">Ask a question</h1>
      <p className="mb-6 text-sm text-muted">
        Answers are grounded in exact clause citations — click any citation to see its
        source.
      </p>
      <ChatInterface />
    </div>
  );
}
