'use client';

import { usePathname } from 'next/navigation';

export function GlobalBranding() {
  const pathname = usePathname();

  // Branding sirf home page par dikhegi
  if (pathname !== '/') {
    return null;
  }

  return (
    <header className="fixed top-0 left-0 z-50 hidden w-full flex-row items-center justify-between p-6 md:flex pointer-events-none">
      
      {/* Left branding */}
      <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/80 px-3.5 py-1.5 shadow-md backdrop-blur-md">
        <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-sm font-bold text-transparent">
          FinSaathi AI
        </span>

        <span className="border-l border-slate-700 pl-2 font-mono text-[10px] text-slate-400">
          Voice for Bharat Challenge
        </span>
      </div>

      {/* Right branding */}
      <span className="pointer-events-auto rounded-full border border-slate-800 bg-slate-900/80 px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-wider text-foreground backdrop-blur-md">
        Powered by{' '}
        <span className="font-semibold text-emerald-400">
          Murf AI
        </span>{' '}
        &{' '}
        <a
          target="_blank"
          rel="noopener noreferrer"
          href="https://docs.livekit.io/agents"
          className="text-emerald-400 underline underline-offset-4"
        >
          LiveKit
        </a>
      </span>
    </header>
  );
}
