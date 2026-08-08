'use client';

import React from 'react';
import { MicOff, AlertTriangle, Lock, RefreshCw, ShieldAlert, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion } from 'motion/react';

interface MicErrorModalProps {
  onRetry: () => void;
  onClose?: () => void;
}

export function MicErrorModal({ onRetry, onClose }: MicErrorModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md"
    >
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl border border-rose-500/30 bg-slate-900/95 p-6 shadow-2xl text-slate-100">
        {/* Top glowing error bar */}
        <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-rose-500 via-amber-500 to-rose-600" />

        <div className="flex flex-col items-center text-center space-y-4 pt-2">
          {/* Mic Off Icon with warning badge */}
          <div className="relative">
            <div className="flex size-20 items-center justify-center rounded-full bg-rose-500/10 border-2 border-rose-500/30 text-rose-400 shadow-[0_0_25px_rgba(244,63,94,0.3)]">
              <MicOff className="size-10" />
            </div>
            <div className="absolute -bottom-1 -right-1 flex size-7 items-center justify-center rounded-full bg-amber-500 text-slate-950 border border-amber-300 shadow">
              <ShieldAlert className="size-4" />
            </div>
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
              Microphone Access Blocked
            </h2>
            <p className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
              FinSaathi AI Voice Assistant
            </p>
          </div>

          <p className="text-sm text-slate-300 leading-relaxed px-2">
            FinSaathi AI requires microphone permission so you can talk with your financial assistant about government schemes, loans, and banking safety.
          </p>

          {/* Detailed step-by-step fix guide */}
          <div className="w-full text-left bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2.5 text-xs text-slate-300">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs pb-1 border-b border-slate-800/80">
              <Lock className="size-4" />
              <span>How to enable your microphone:</span>
            </div>
            
            <ol className="space-y-2 list-decimal list-inside text-slate-300">
              <li className="leading-snug">
                Look at your browser's address bar at the top left.
              </li>
              <li className="leading-snug">
                Click the <span className="font-semibold text-amber-300">Lock 🔒</span> or <span className="font-semibold text-amber-300">Tune 🎛️</span> icon next to the website address.
              </li>
              <li className="leading-snug">
                Find <span className="font-semibold text-emerald-400">Microphone</span> and switch the setting to <span className="font-semibold text-emerald-400">"Allow"</span>.
              </li>
              <li className="leading-snug">
                Click the <span className="font-semibold text-sky-400">"Try Again"</span> button below.
              </li>
            </ol>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 w-full pt-2">
            <Button
              onClick={onRetry}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold rounded-xl py-5 shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2"
            >
              <RefreshCw className="size-4 animate-spin-hover" />
              <span>Try Again</span>
            </Button>
            {onClose && (
              <Button
                variant="outline"
                onClick={onClose}
                className="w-full border-slate-700 hover:bg-slate-800 text-slate-300 rounded-xl py-5"
              >
                Dismiss
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
