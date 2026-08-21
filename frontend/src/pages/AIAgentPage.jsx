import React from 'react';
import AIAgentChat from '../components/AIAgentChat';

export default function AIAgentPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <AIAgentChat />
    </div>
  );
}
