'use client';

import { useEffect, useState } from 'react';

type Analytics = {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
};

const API_URL = 'http://127.0.0.1:8000';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] =
    useState<Analytics | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState('');

  async function loadAnalytics() {
    try {
      setLoading(true);
      setError('');

      const response = await fetch(
        `${API_URL}/api/analytics`,
        {
          cache: 'no-store',
        }
      );

      if (!response.ok) {
        throw new Error(
          `API returned ${response.status}`
        );
      }

      const data =
        await response.json();

      setAnalytics(
        data.analytics
      );

    } catch (err) {
      console.error(
        'Failed to load analytics:',
        err
      );

      setError(
        'Unable to connect to the analytics API. Make sure FastAPI is running on port 8000.'
      );

    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, []);

  return (
    <main className="min-h-screen bg-[#050607] text-white">

      {/* Background glow */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <div className="absolute left-1/2 top-[-180px] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-emerald-400/10 blur-[120px]" />

        <div className="absolute bottom-[-150px] right-[-100px] h-[350px] w-[350px] rounded-full bg-cyan-400/5 blur-[120px]" />

      </div>


      <div className="relative mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10">

        {/* HEADER */}

        <header className="mb-12 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">

          <div>

            <div className="mb-5 inline-flex items-center gap-3 rounded-full border border-white/10 bg-[#11151c] px-4 py-2">

              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-400/10">

                <span className="text-sm text-emerald-400">
                  ₹
                </span>

              </div>

              <span className="text-sm font-bold text-emerald-400">
                FinSaathi AI
              </span>

              <span className="text-xs text-white/40">
                Analytics
              </span>

            </div>


            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">

              Call{' '}

              <span className="text-emerald-400">
                Analytics
              </span>

            </h1>


            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/50 sm:text-base">

              Monitor how successfully FinSaathi
              AI is handling user conversations.

            </p>

          </div>


          <button
            onClick={loadAnalytics}
            className="w-fit rounded-full border border-emerald-400/30 bg-emerald-400/10 px-5 py-2.5 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-400/20"
          >
            ↻ Refresh
          </button>

        </header>


        {/* ERROR */}

        {error && (

          <div className="mb-8 rounded-2xl border border-red-400/20 bg-red-400/5 p-5 text-sm text-red-300">

            <div className="flex items-start gap-3">

              <span className="text-lg">
                ⚠
              </span>

              <div>

                <p className="font-semibold">
                  Connection Error
                </p>

                <p className="mt-1 text-red-300/70">
                  {error}
                </p>

              </div>

            </div>

          </div>

        )}


        {/* LOADING */}

        {loading && (

          <div className="rounded-3xl border border-white/10 bg-[#0c1016]/80 p-16 text-center backdrop-blur-xl">

            <div className="mx-auto mb-5 h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-emerald-400" />

            <p className="text-sm text-white/50">
              Loading call analytics...
            </p>

          </div>

        )}


        {/* ANALYTICS */}

        {!loading &&
          !error &&
          analytics && (

            <div>

              {/* Three required metrics */}

              <div className="grid gap-5 md:grid-cols-3">

                {/* TOTAL */}

                <div className="rounded-3xl border border-white/10 bg-[#0b0f15]/90 p-7 shadow-2xl backdrop-blur-xl transition hover:border-white/20">

                  <div className="flex items-center justify-between">

                    <div>

                      <p className="text-xs font-bold uppercase tracking-widest text-white/35">
                        Total Calls
                      </p>

                      <p className="mt-4 text-5xl font-extrabold tracking-tight">
                        {
                          analytics.total_calls
                        }
                      </p>

                    </div>


                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-2xl">
                      ☎
                    </div>

                  </div>


                  <p className="mt-6 text-sm text-white/40">
                    Total conversations recorded
                  </p>

                </div>


                {/* SUCCESS */}

                <div className="rounded-3xl border border-emerald-400/15 bg-[#0b0f15]/90 p-7 shadow-2xl backdrop-blur-xl transition hover:border-emerald-400/30">

                  <div className="flex items-center justify-between">

                    <div>

                      <p className="text-xs font-bold uppercase tracking-widest text-emerald-400/60">
                        Successful Calls
                      </p>

                      <p className="mt-4 text-5xl font-extrabold tracking-tight text-emerald-300">
                        {
                          analytics.successful_calls
                        }
                      </p>

                    </div>


                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-2xl text-emerald-400">
                      ✓
                    </div>

                  </div>


                  <p className="mt-6 text-sm text-white/40">
                    Calls that achieved the success condition
                  </p>

                </div>


                {/* FAILED */}

                <div className="rounded-3xl border border-red-400/10 bg-[#0b0f15]/90 p-7 shadow-2xl backdrop-blur-xl transition hover:border-red-400/20">

                  <div className="flex items-center justify-between">

                    <div>

                      <p className="text-xs font-bold uppercase tracking-widest text-red-300/50">
                        Failed Calls
                      </p>

                      <p className="mt-4 text-5xl font-extrabold tracking-tight text-red-300">
                        {
                          analytics.failed_calls
                        }
                      </p>

                    </div>


                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-red-400/20 bg-red-400/10 text-2xl text-red-300">
                      ×
                    </div>

                  </div>


                  <p className="mt-6 text-sm text-white/40">
                    Calls that did not reach the success condition
                  </p>

                </div>

              </div>


              {/* SUCCESS CONDITION */}

              <div className="mt-8 rounded-3xl border border-white/10 bg-[#0b0f15]/90 p-7 backdrop-blur-xl">

                <div className="flex items-start gap-4">

                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-400/10 text-emerald-400">
                    ✦
                  </div>


                  <div>

                    <p className="text-xs font-bold uppercase tracking-widest text-emerald-400/60">
                      Success Condition
                    </p>

                    <p className="mt-2 text-sm leading-6 text-white/60">

                      A call is considered successful
                      when the requested financial-scheme
                      eligibility check is successfully
                      completed.

                    </p>

                  </div>

                </div>

              </div>

            </div>

          )}

      </div>

    </main>
  );
}
