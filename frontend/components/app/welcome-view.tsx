'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { FinAvatar } from '@/components/app/fin-avatar';
import { Shield, Landmark, CreditCard, Lock, PhoneCall, Sparkles, ChevronRight } from 'lucide-react';
import { motion } from 'motion/react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  isConnecting?: boolean;
  micError?: boolean;
  onOpenMicError?: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  isConnecting = false,
  micError = false,
  onOpenMicError,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="w-full max-w-4xl mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-[85vh]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full flex flex-col items-center text-center space-y-8"
      >
        {/* Top FinSaathi Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-emerald-500/30 bg-emerald-950/40 text-emerald-300 text-xs font-medium tracking-wide backdrop-blur-md shadow-sm">
          <Sparkles className="size-3.5 text-amber-400 animate-pulse" />
          <span>FinSaathi AI &bull; Murf AI Voice for Bharat</span>
        </div>

        {/* Financial Assistant Avatar */}
        <FinAvatar state="ready" size="xl" showBadge={true} />

        {/* Title & Subtitle */}
        <div className="space-y-3 max-w-2xl">
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-emerald-100 to-teal-300 bg-clip-text text-transparent">
            FinSaathi AI
          </h1>
          <p className="text-sm sm:text-lg text-slate-300 font-normal leading-relaxed">
            Your Multilingual AI Financial Services Assistant for schemes, loans, insurance & banking safety.
          </p>
          <p className="text-xs text-slate-400 font-mono">
            Developed by <span className="text-emerald-400 font-semibold">Nipun Goel</span>
          </p>
        </div>

        {/* Capabilities Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-3xl pt-2">
          <div className="flex flex-col items-center p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm text-center transition-colors hover:border-emerald-500/40">
            <Landmark className="size-6 text-emerald-400 mb-2" />
            <span className="text-xs font-bold text-slate-200">Govt Schemes</span>
            <span className="text-[11px] text-slate-400 mt-1">PM-Kisan, Mudra & Pensions</span>
          </div>

          <div className="flex flex-col items-center p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm text-center transition-colors hover:border-emerald-500/40">
            <CreditCard className="size-6 text-emerald-400 mb-2" />
            <span className="text-xs font-bold text-slate-200">Loans & Banking</span>
            <span className="text-[11px] text-slate-400 mt-1">Eligibility & Application steps</span>
          </div>

          <div className="flex flex-col items-center p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm text-center transition-colors hover:border-emerald-500/40">
            <Shield className="size-6 text-emerald-400 mb-2" />
            <span className="text-xs font-bold text-slate-200">Insurance Info</span>
            <span className="text-[11px] text-slate-400 mt-1">Health, Life & Claims</span>
          </div>

          <div className="flex flex-col items-center p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm text-center transition-colors hover:border-emerald-500/40">
            <Lock className="size-6 text-amber-400 mb-2" />
            <span className="text-xs font-bold text-slate-200">Fraud Safety</span>
            <span className="text-[11px] text-slate-400 mt-1">OTP/PIN protection & safe UPI</span>
          </div>
        </div>

        {/* ONE CLEAR BUTTON to Begin (Step 2 - Ready state requirement) */}
        <div className="pt-4 flex flex-col items-center w-full max-w-sm">
          <Button
            size="lg"
            onClick={onStartCall}
            disabled={isConnecting}
            className="w-full h-14 rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-base shadow-[0_0_30px_rgba(16,185,129,0.4)] transition-all duration-300 transform hover:scale-[1.02] flex items-center justify-center gap-3 cursor-pointer"
          >
            <PhoneCall className="size-5 fill-slate-950 text-slate-950 animate-bounce" />
            <span>{startButtonText || 'Start Call with FinSaathi AI'}</span>
            <ChevronRight className="size-5" />
          </Button>

          <p className="text-xs text-slate-400 mt-3 flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
            Ready for Hindi, English & Hinglish voice input
          </p>
        </div>

        {/* Microphone warning indicator if mic blocked */}
        {micError && (
          <div className="w-full max-w-md p-3 rounded-xl border border-rose-500/40 bg-rose-950/40 text-rose-300 text-xs flex items-center justify-between gap-3">
            <span>Microphone access issue detected.</span>
            <button
              onClick={onOpenMicError}
              className="underline font-semibold hover:text-rose-200"
            >
              Fix Permissions
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};
