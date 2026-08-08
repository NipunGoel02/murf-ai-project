'use client';

import React from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, Banknote, Landmark, Volume2, Mic, CheckCircle2, PhoneOff, Loader2 } from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';

export type AgentDisplayState = 'ready' | 'connecting' | 'listening' | 'speaking' | 'thinking' | 'ended';

interface FinAvatarProps {
  state: AgentDisplayState;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showBadge?: boolean;
  className?: string;
}

export function FinAvatar({ state, size = 'lg', showBadge = true, className }: FinAvatarProps) {
  const sizeClasses = {
    sm: 'size-12 text-xs',
    md: 'size-20 text-sm',
    lg: 'size-28 text-base',
    xl: 'size-36 text-lg',
  };

  const iconSizes = {
    sm: 20,
    md: 32,
    lg: 44,
    xl: 56,
  };

  const getRingColor = () => {
    switch (state) {
      case 'speaking':
        return 'border-emerald-500 shadow-[0_0_25px_rgba(16,185,129,0.5)] bg-emerald-950/20';
      case 'listening':
        return 'border-sky-500 shadow-[0_0_25px_rgba(14,165,233,0.5)] bg-sky-950/20';
      case 'connecting':
      case 'thinking':
        return 'border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.4)] bg-amber-950/20';
      case 'ended':
        return 'border-slate-600 bg-slate-900/40 opacity-75';
      case 'ready':
      default:
        return 'border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.25)] bg-slate-900/50';
    }
  };

  const getBadgeContent = () => {
    switch (state) {
      case 'speaking':
        return {
          icon: <Volume2 className="size-3.5 text-emerald-400 animate-pulse" />,
          text: 'FinSaathi Speaking',
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        };
      case 'listening':
        return {
          icon: <Mic className="size-3.5 text-sky-400 animate-bounce" />,
          text: 'Listening to you',
          bg: 'bg-sky-500/10 border-sky-500/30 text-sky-300',
        };
      case 'thinking':
        return {
          icon: <Loader2 className="size-3.5 text-amber-400 animate-spin" />,
          text: 'FinSaathi Thinking...',
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
        };
      case 'connecting':
        return {
          icon: <Loader2 className="size-3.5 text-amber-400 animate-spin" />,
          text: 'Connecting...',
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
        };
      case 'ended':
        return {
          icon: <PhoneOff className="size-3.5 text-rose-400" />,
          text: 'Call Ended',
          bg: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
        };
      case 'ready':
      default:
        return {
          icon: <CheckCircle2 className="size-3.5 text-emerald-400" />,
          text: 'FinSaathi Ready',
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        };
    }
  };

  const badge = getBadgeContent();

  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <div className="relative flex items-center justify-center">
        {/* Animated outer pulsing ring for active states */}
        {(state === 'speaking' || state === 'listening' || state === 'connecting' || state === 'thinking') && (
          <motion.div
            animate={{
              scale: state === 'speaking' ? [1, 1.15, 1] : [1, 1.08, 1],
              opacity: [0.3, 0.7, 0.3],
            }}
            transition={{
              duration: state === 'speaking' ? 1.5 : 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className={cn(
              'absolute inset-0 rounded-full border-2',
              state === 'speaking' && 'border-emerald-400/50',
              state === 'listening' && 'border-sky-400/50',
              (state === 'connecting' || state === 'thinking') && 'border-amber-400/50'
            )}
          />
        )}

        {/* Main Avatar Circle */}
        <div
          className={cn(
            'relative flex items-center justify-center rounded-full border-2 transition-all duration-300 backdrop-blur-md',
            sizeClasses[size],
            getRingColor()
          )}
        >
          {/* Financial Avatar Graphic */}
          <div className="relative flex items-center justify-center text-emerald-400">
            <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-teal-400/10 rounded-full blur-sm" />
            <div className="relative flex flex-col items-center justify-center">
              <div className="relative">
                <Landmark size={iconSizes[size]} className="text-emerald-400 drop-shadow-[0_2px_8px_rgba(16,185,129,0.4)]" />
                <span className="absolute -bottom-1 -right-1 font-bold text-[10px] bg-amber-500 text-slate-950 px-1 py-0.2 rounded-full leading-none border border-amber-300 shadow">
                  ₹
                </span>
              </div>
            </div>
          </div>

          {/* Status Indicator Dot */}
          <span
            className={cn(
              'absolute bottom-0 right-0 rounded-full border-2 border-slate-900',
              size === 'sm' && 'size-3.5',
              size === 'md' && 'size-5',
              size === 'lg' && 'size-6',
              size === 'xl' && 'size-7',
              state === 'speaking' && 'bg-emerald-500 shadow-[0_0_10px_#10b981]',
              state === 'listening' && 'bg-sky-500 shadow-[0_0_10px_#06b6d4]',
              (state === 'connecting' || state === 'thinking') && 'bg-amber-500 shadow-[0_0_10px_#f59e0b]',
              state === 'ended' && 'bg-slate-500',
              state === 'ready' && 'bg-emerald-400'
            )}
          />
        </div>
      </div>

      {showBadge && (
        <div
          className={cn(
            'flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold tracking-wide backdrop-blur-md shadow-sm transition-all duration-300',
            badge.bg
          )}
        >
          {badge.icon}
          <span>{badge.text}</span>
        </div>
      )}
    </div>
  );
}
