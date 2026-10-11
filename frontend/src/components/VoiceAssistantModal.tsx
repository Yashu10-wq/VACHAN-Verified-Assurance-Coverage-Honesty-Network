import React, { useState } from 'react';
import { Mic, X, Send, Sparkles, Volume2, Bot } from 'lucide-react';

export const VoiceAssistantModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string; isVoice?: boolean }>>([
    {
      sender: 'assistant',
      text: 'Hello Rahul! I am your VoiceGuard Policy Assistant powered by ElevenLabs. You can ask me about coverage clauses, waiting periods, or why your claim was adjusted.',
    },
  ]);

  const handleSend = (textToSend?: string) => {
    const text = textToSend || query;
    if (!text.trim()) return;

    const userMsg = { sender: 'user' as const, text };
    setMessages((prev) => [...prev, userMsg]);
    setQuery('');

    // Simulated intelligent response based on policy knowledge
    setTimeout(() => {
      let reply = 'Our deterministic policy engine verifies that all claims are evaluated against underwritten schedule clauses.';
      if (text.toLowerCase().includes('knee') || text.toLowerCase().includes('waiting')) {
        reply = 'Clause 4.2 under CarePlus specifies a 24-month waiting period for joint replacements. The agent verbal promise of zero-waiting period was flagged as CONTRADICTED during your Vaada consultation check.';
      } else if (text.toLowerCase().includes('claim') || text.toLowerCase().includes('excess')) {
        reply = 'Claim #CLM-2026-8812 exceeded the single-rehabilitation sub-limit of ₹50,000. An excess of ₹20,000 was deducted while approving the maximum allowable ₹50,000.';
      }
      setMessages((prev) => [...prev, { sender: 'assistant', text: reply, isVoice: true }]);
    }, 600);
  };

  return (
    <>
      {/* Floating Pill Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-5 py-3 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-600/30 hover:shadow-violet-600/50 hover:scale-105 transition-all active:scale-98"
      >
        <Mic className="w-4 h-4 animate-pulse" />
        <span className="text-xs font-bold tracking-wide">Ask VoiceGuard</span>
      </button>

      {/* Assistant Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-sm flex items-end sm:items-center justify-end sm:justify-center p-4">
          <div className="bg-white rounded-3xl w-full max-w-md h-[520px] flex flex-col border border-slate-200 shadow-float overflow-hidden">
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-violet-600 to-indigo-600 text-white flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold">VoiceGuard AI Assistant</h4>
                  <p className="text-[10px] text-violet-200">ElevenLabs Spoken Explainability</p>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Message Area */}
            <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/60 text-xs">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded-2xl max-w-[85%] leading-relaxed ${
                    m.sender === 'user'
                      ? 'ml-auto bg-brand-600 text-white rounded-br-none'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-none shadow-sm'
                  }`}
                >
                  <p>{m.text}</p>
                  {m.isVoice && (
                    <div className="mt-2 flex items-center gap-1.5 text-[10px] text-violet-600 font-bold">
                      <Volume2 className="w-3 h-3" />
                      <span>Synthesizing voice response...</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Quick Questions Chips */}
            <div className="p-2.5 bg-white border-t border-slate-100 flex gap-1.5 overflow-x-auto text-[11px]">
              <button
                onClick={() => handleSend('Is knee surgery covered?')}
                className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap transition"
              >
                Is knee surgery covered?
              </button>
              <button
                onClick={() => handleSend('Why was my claim adjusted?')}
                className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 whitespace-nowrap transition"
              >
                Why was my claim adjusted?
              </button>
            </div>

            {/* Input Box */}
            <div className="p-3 bg-white border-t border-slate-100 flex items-center gap-2">
              <input
                type="text"
                placeholder="Ask anything about policy clauses or claims..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                className="flex-1 px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs outline-none focus:border-violet-600"
              />
              <button
                onClick={() => handleSend()}
                className="p-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
