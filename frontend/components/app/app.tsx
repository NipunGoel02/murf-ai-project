'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const tokenSource = useMemo(() => {
    return typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string'
      ? getSandboxTokenSource(appConfig)
      : TokenSource.endpoint('/api/token');
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName
      ? { agentName: appConfig.agentName }
      : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />

      <main className="relative grid h-svh grid-cols-1 place-content-center">

        {/* ================================================= */}
        {/* MAIN AI AGENT */}
        {/* ================================================= */}

        <ViewController appConfig={appConfig} />


        {/* ================================================= */}
        {/* TOP NAVIGATION */}
        {/* ================================================= */}

        <div className="fixed right-[260px] top-6 z-50 flex items-center gap-2">

          {/* Human Support */}

          <Link
            href="/escalations"
            className="group flex items-center gap-2 rounded-full border border-white/10 bg-[#11151c]/95 px-4 py-2 text-xs font-semibold text-white shadow-lg backdrop-blur-xl transition-all duration-200 hover:border-emerald-400/40 hover:bg-[#182019]"
          >
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-400/10 text-sm">
              🤝
            </span>

            <span className="whitespace-nowrap">
              Human Support
            </span>
          </Link>


          {/* Call Analytics */}

          <Link
            href="/analytics"
            className="group flex items-center gap-2 rounded-full border border-white/10 bg-[#11151c]/95 px-4 py-2 text-xs font-semibold text-white shadow-lg backdrop-blur-xl transition-all duration-200 hover:border-emerald-400/40 hover:bg-[#182019]"
          >
            <span className="flex   h-5 w-5 items-center justify-center rounded-full bg-emerald-400/10 text-sm">
              📊
            </span>

            <span className="whitespace-nowrap">
              Analytics
            </span>
          </Link>

        </div>


        {/* ================================================= */}
        {/* AUDIO */}
        {/* ================================================= */}

        <StartAudioButton label="Start Audio" />


        {/* ================================================= */}
        {/* TOASTER */}
        {/* ================================================= */}

        <Toaster
          icons={{
            warning: (
              <WarningIcon weight="bold" />
            ),
          }}
          position="top-center"
          className="toaster group"
          style={
            {
              '--normal-bg': 'var(--popover)',
              '--normal-text': 'var(--popover-foreground)',
              '--normal-border': 'var(--border)',
            } as React.CSSProperties
          }
        />

      </main>
    </AgentSessionProvider>
  );
}
