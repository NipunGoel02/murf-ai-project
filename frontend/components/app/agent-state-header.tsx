'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useAgent, useSessionContext, useTrackVolume } from '@livekit/components-react';
import { ConnectionState, Track } from 'livekit-client';
import { FinAvatar, AgentDisplayState } from '@/components/app/fin-avatar';
import { Mic, Volume2, Loader2, PhoneOff, User, Sparkles } from 'lucide-react';
import { useLocalTrackRef } from '@/components/agents-ui/blocks/agent-session-view-01/components/tile-view';

interface AgentStateHeaderProps {
  onEndCall?: () => void;
  onRestartCall?: () => void;
}

export function AgentStateHeader({ onEndCall, onRestartCall }: AgentStateHeaderProps) {
  const session = useSessionContext();
  const { state: agentState } = useAgent();
  const micTrack = useLocalTrackRef(Track.Source.Microphone);
  const userVolume = useTrackVolume(micTrack);

  const isConnecting = session.connectionState === ConnectionState.Connecting;

  // Determine current display state among the 5 required states
  let currentState: AgentDisplayState = 'ready';
  if (!session.isConnected && !isConnecting) {
    currentState = 'ended';
  } else if (isConnecting || agentState === 'connecting' || agentState === 'initializing' || agentState === undefined) {
    currentState = 'connecting';
  } else if (agentState === 'speaking') {
    currentState = 'speaking';
  } else if (agentState === 'thinking') {
    currentState = 'thinking';
  } else if (agentState === 'listening' || session.isConnected) {
    currentState = 'listening';
  }

  // Calculate volume percentage for user microphone volume bar (0-100%)
  const userVolumePercent = Math.min(100, Math.max(0, Math.round(userVolume * 100 * 2.5)));

  return (
    <div className="w-full flex flex-col items-center justify-center space-y-3 py-3 px-4 z-40">
      {/* Top Banner highlighting current state */}
      <AnimatePresence mode="wait">
        {/* State 2: Connecting */}
        {currentState === 'connecting' && (
          <motion.div
            key="state-connecting"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-amber-950/70 border border-amber-500/40 text-amber-200 shadow-lg backdrop-blur-md"
          >
            <Loader2 className="size-5 text-amber-400 animate-spin" />
            <div className="flex flex-col text-left">
              <span className="text-sm font-bold text-amber-100">Connecting to FinSaathi AI...</span>
              <span className="text-xs text-amber-300/80">Please wait while we set up your financial call</span>
            </div>
          </motion.div>
        )}

        {/* State 3: Listening (User is speaking or agent is listening) */}
        {currentState === 'listening' && (
          <motion.div
            key="state-listening"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex flex-col items-center gap-2 px-6 py-3 rounded-2xl bg-sky-950/80 border border-sky-500/40 text-sky-200 shadow-xl backdrop-blur-md max-w-md w-full"
          >
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <div className="flex size-7 items-center justify-center rounded-full bg-sky-500/20 text-sky-400">
                  <User className="size-4 animate-bounce" />
                </div>
                <span className="text-sm font-bold text-sky-100">Listening to you</span>
              </div>
              <span className="text-xs font-semibold text-sky-400 bg-sky-950 px-2 py-0.5 rounded-full border border-sky-500/30">
                You are speaking
              </span>
            </div>

            {/* Volume Bar (Step 3 Requirement) */}
            <div className="w-full flex items-center gap-3 pt-1">
              <Mic className="size-4 text-sky-400 shrink-0" />
              <div className="flex-1 h-2.5 bg-slate-900 rounded-full overflow-hidden border border-sky-500/20 p-0.5">
                <motion.div
                  className="h-full bg-gradient-to-r from-sky-500 to-cyan-400 rounded-full shadow-[0_0_10px_#38bdf8]"
                  animate={{ width: `${Math.max(8, userVolumePercent)}%` }}
                  transition={{ duration: 0.1, ease: 'easeOut' }}
                />
              </div>
              <span className="text-[11px] font-mono font-bold text-sky-300 min-w-[32px] text-right">
                {userVolumePercent}%
              </span>
            </div>
          </motion.div>
        )}

        {/* State 4: Speaking (Agent is replying) */}
        {currentState === 'speaking' && (
          <motion.div
            key="state-speaking"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex items-center gap-3 px-6 py-3 rounded-2xl bg-emerald-950/80 border border-emerald-500/50 text-emerald-200 shadow-xl backdrop-blur-md"
          >
            <div className="flex size-8 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
              <Volume2 className="size-5 animate-pulse" />
            </div>
            <div className="flex flex-col text-left">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-emerald-100">FinSaathi AI is speaking</span>
                <span className="flex size-2 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <span className="text-xs text-emerald-300/90">Agent is replying to your query</span>
            </div>

            {/* Animated Waveform Indicator Bars for Agent */}
            <div className="flex items-end gap-1 h-5 ml-2">
              <motion.span animate={{ height: ['40%', '100%', '30%'] }} transition={{ repeat: Infinity, duration: 0.6 }} className="w-1 bg-emerald-400 rounded-full" />
              <motion.span animate={{ height: ['80%', '20%', '90%'] }} transition={{ repeat: Infinity, duration: 0.5 }} className="w-1 bg-emerald-400 rounded-full" />
              <motion.span animate={{ height: ['30%', '90%', '40%'] }} transition={{ repeat: Infinity, duration: 0.7 }} className="w-1 bg-emerald-400 rounded-full" />
              <motion.span animate={{ height: ['100%', '40%', '80%'] }} transition={{ repeat: Infinity, duration: 0.4 }} className="w-1 bg-emerald-400 rounded-full" />
            </div>
          </motion.div>
        )}

        {/* State: Thinking */}
        {currentState === 'thinking' && (
          <motion.div
            key="state-thinking"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-amber-950/70 border border-amber-500/40 text-amber-200 shadow-lg backdrop-blur-md"
          >
            <Sparkles className="size-4 text-amber-400 animate-spin" />
            <span className="text-sm font-bold text-amber-100">FinSaathi AI is thinking...</span>
          </motion.div>
        )}

        {/* State 5: Call Ended */}
        {currentState === 'ended' && (
          <motion.div
            key="state-ended"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center gap-3 p-5 rounded-2xl bg-slate-900/90 border border-slate-700 text-slate-200 shadow-2xl backdrop-blur-md max-w-sm w-full text-center"
          >
            <div className="flex size-12 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30">
              <PhoneOff className="size-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">Call Ended</h3>
              <p className="text-xs text-slate-400">The conversation with FinSaathi AI has finished.</p>
            </div>
            {onRestartCall && (
              <button
                onClick={onRestartCall}
                className="mt-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-950/40 transition-all"
              >
                Start New Call
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
