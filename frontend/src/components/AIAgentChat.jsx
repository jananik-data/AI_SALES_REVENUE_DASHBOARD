import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, 
  User, 
  Send, 
  Sparkles, 
  Wrench, 
  CheckCircle2, 
  Lightbulb,
  CornerDownLeft,
  PlusCircle,
  RotateCcw
} from 'lucide-react';
import api from '../api/client';

const SUGGESTIONS = [
  'Which product is performing best?',
  'Why?',
  'How are the regions performing?',
  'Compare South and West.',
  'Why did revenue decrease?',
  'Predict next month\'s revenue.',
  'What should I do next month?'
];

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  message: `Hello! I'm your **AI Sales Analyst**.\n\nI have direct access to your real-time sales data and trained ML prediction models. Ask me anything about your products, regional sales, growth trends, or future revenue forecasts.`,
  tool_calls: [],
  created_at: new Date().toISOString()
};

export default function AIAgentChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/ai/chat-history');
      if (res.data && res.data.length > 0) {
        setMessages(res.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearChat = async () => {
    try {
      await api.delete('/ai/chat-history');
      setMessages([WELCOME_MESSAGE]);
    } catch (err) {
      console.error('Failed to clear chat history', err);
      setMessages([WELCOME_MESSAGE]);
    }
  };

  const handleSend = async (textToSend) => {
    const question = (textToSend || input).trim();
    if (!question || isLoading) return;

    setInput('');
    const userMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      message: question,
      tool_calls: [],
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await api.post('/ai/chat', { message: question });
      const assistantMsg = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        message: res.data.reply,
        tool_calls: res.data.tool_calls || [],
        generated_at: res.data.generated_at
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          message: "I couldn't complete that analysis right now. Please try again.",
          tool_calls: [],
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to parse inline **bold** and *italic*
  const formatInlineText = (text) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#fff', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={i} style={{ color: '#cbd5e1' }}>{part.slice(1, -1)}</em>;
      }
      return part;
    });
  };

  // Render markdown-like sections cleanly
  const renderMessageContent = (content) => {
    return (
      <div style={{ lineHeight: '1.6', fontSize: '13.5px' }}>
        {content.split('\n').map((line, idx) => {
          if (line.startsWith('### ')) {
            return <h3 key={idx} style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', margin: '10px 0 4px' }}>{line.replace('### ', '')}</h3>;
          }
          if (line.startsWith('#### ')) {
            return <h4 key={idx} style={{ fontSize: '14px', fontWeight: 600, color: '#a5b4fc', margin: '8px 0 4px' }}>{line.replace('#### ', '')}</h4>;
          }
          if (line.startsWith('- ')) {
            return (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', margin: '4px 0 4px 6px' }}>
                <span style={{ color: '#818cf8', fontWeight: 700 }}>•</span>
                <span>{formatInlineText(line.replace('- ', ''))}</span>
              </div>
            );
          }
          if (/^\d+\.\s/.test(line)) {
            const num = line.match(/^\d+\./)[0];
            const rest = line.replace(/^\d+\.\s*/, '');
            return (
              <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', margin: '6px 0 6px 4px' }}>
                <span style={{ color: '#38bdf8', fontWeight: 700, minWidth: '18px' }}>{num}</span>
                <span>{formatInlineText(rest)}</span>
              </div>
            );
          }
          if (line.trim() === '') {
            return <div key={idx} style={{ height: '6px' }} />;
          }
          return <p key={idx} style={{ margin: '4px 0' }}>{formatInlineText(line)}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="glass-card" style={{ height: '700px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Agent Chat Header */}
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid var(--border-glass)',
        background: 'rgba(15, 23, 42, 0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
          }}>
            <Bot size={22} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>AI Sales Analyst Agent</span>
              <span className="badge badge-primary" style={{ fontSize: '10px' }}>Agentic</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Conversational sales reasoning, KPI insights & ML revenue predictions
            </div>
          </div>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={handleClearChat}
          title="Start a new chat session"
        >
          <RotateCcw size={13} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Message Stream */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {messages.map((msg, index) => {
          const isAi = msg.role === 'assistant';
          return (
            <div
              key={msg.id || index}
              style={{
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start',
                alignSelf: isAi ? 'flex-start' : 'flex-end',
                maxWidth: isAi ? '85%' : '75%'
              }}
            >
              {isAi && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '4px'
                }}>
                  <Bot size={16} color="#fff" />
                </div>
              )}

              <div style={{
                background: isAi ? 'rgba(26, 37, 65, 0.7)' : 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                border: isAi ? '1px solid var(--border-glass)' : 'none',
                borderRadius: isAi ? '12px 12px 12px 2px' : '12px 12px 2px 12px',
                padding: '14px 18px',
                color: '#fff',
                boxShadow: isAi ? '0 4px 16px rgba(0,0,0,0.2)' : '0 4px 14px rgba(99, 102, 241, 0.3)'
              }}>
                {/* Render Tool Invocations if any */}
                {isAi && msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div style={{
                    marginBottom: '10px',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: '#38bdf8'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px', fontWeight: 600, color: '#a5b4fc' }}>
                      <Wrench size={11} /> Agent Tools Executed:
                    </div>
                    {msg.tool_calls.map((t, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#94a3b8' }}>
                        <span>⚡</span>
                        <code>{t.tool_name}</code>
                      </div>
                    ))}
                  </div>
                )}

                {/* Message Body */}
                {renderMessageContent(msg.message)}
              </div>

              {!isAi && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '4px'
                }}>
                  <User size={16} color="#fff" />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={16} color="#fff" />
            </div>
            <div style={{ background: 'rgba(26, 37, 65, 0.7)', padding: '12px 18px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: '#a5b4fc', fontSize: '13px' }}>
              <Sparkles size={14} className="animate-spin" />
              <span>Analyzing sales metrics & formulating answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      <div style={{
        padding: '10px 24px',
        borderTop: '1px solid var(--border-glass)',
        background: 'rgba(15, 23, 42, 0.5)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        overflowX: 'auto',
        whiteSpace: 'nowrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
          <Lightbulb size={12} color="#fbbf24" /> Suggested:
        </div>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            style={{
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-glass)',
              color: 'var(--text-secondary)',
              fontSize: '11.5px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontFamily: 'inherit'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Chat Input Bar */}
      <div style={{ padding: '16px 24px', background: 'rgba(15, 23, 42, 0.9)', borderTop: '1px solid var(--border-glass)' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{ display: 'flex', gap: '12px' }}
        >
          <input
            type="text"
            className="form-input"
            placeholder="Ask a sales question, request an explanation or forecast..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            style={{ flex: 1 }}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!input.trim() || isLoading}
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
