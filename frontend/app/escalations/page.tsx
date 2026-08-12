'use client';

import { useEffect, useState } from 'react';

type Escalation = {
  request_id: string;
  user_id: string;
  reason: string;
  summary: string;
  what_checked: string | null;
  urgency: string;
  language: string | null;
  preferred_followup: string | null;
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED';
  created_at: string;
  resolution: string | null;
  resolved_at: string | null;
};

const API_URL = 'http://127.0.0.1:8000';

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  async function loadEscalations() {
    try {
      setLoading(true);
      setError('');

      const response = await fetch(
        `${API_URL}/api/escalations`,
        {
          cache: 'no-store',
        }
      );

      if (!response.ok) {
        throw new Error(
          `API returned ${response.status}`
        );
      }

      const data = await response.json();

      setEscalations(
        data.escalations || []
      );
    } catch (err) {
      console.error(err);

      setError(
        'Unable to connect to the support API. Make sure the FastAPI server is running on port 8000.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEscalations();
  }, []);

  async function updateStatus(
    requestId: string,
    status: 'IN_PROGRESS' | 'RESOLVED'
  ) {
    try {
      setUpdating(requestId);
      setError('');

      let resolution: string | null = null;

      if (status === 'RESOLVED') {
        const enteredResolution =
          window.prompt(
            'Enter the resolution provided to the user:'
          );

        if (!enteredResolution?.trim()) {
          setUpdating(null);
          return;
        }

        resolution = enteredResolution.trim();
      }

      const response = await fetch(
        `${API_URL}/api/escalations/${requestId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status,
            resolution,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            'Failed to update escalation'
        );
      }

      await loadEscalations();
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : 'Failed to update escalation.'
      );
    } finally {
      setUpdating(null);
    }
  }

  function statusStyle(
    status: Escalation['status']
  ) {
    if (status === 'OPEN') {
      return {
        badge:
          'border-red-400/30 bg-red-400/10 text-red-300',
        dot: 'bg-red-400',
      };
    }

    if (status === 'IN_PROGRESS') {
      return {
        badge:
          'border-yellow-400/30 bg-yellow-400/10 text-yellow-300',
        dot: 'bg-yellow-400',
      };
    }

    return {
      badge:
        'border-emerald-400/30 bg-emerald-400/10 text-emerald-300',
      dot: 'bg-emerald-400',
    };
  }

  function urgencyStyle(
    urgency: string
  ) {
    const value =
      urgency.toUpperCase();

    if (value === 'HIGH') {
      return 'border-red-400/30 bg-red-400/10 text-red-300';
    }

    if (value === 'EMERGENCY') {
      return 'border-red-500/40 bg-red-500/15 text-red-300';
    }

    if (value === 'MEDIUM') {
      return 'border-yellow-400/30 bg-yellow-400/10 text-yellow-300';
    }

    return 'border-white/10 bg-white/5 text-white/60';
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#050607] text-white">

      {/* Background glow */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <div className="absolute left-1/2 top-[-180px] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-emerald-400/10 blur-[120px]" />

        <div className="absolute bottom-[-150px] right-[-100px] h-[350px] w-[350px] rounded-full bg-cyan-400/5 blur-[120px]" />

      </div>


      <div className="relative mx-auto max-w-7xl px-5 py-7 sm:px-8 lg:px-10">

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <header className="mb-10 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">

          <div>

            {/* Brand */}

            <div className="mb-5 inline-flex items-center gap-3 rounded-full border border-white/10 bg-[#11151c] px-4 py-2 shadow-lg">

              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-400/10">

                <span className="text-sm text-emerald-400">
                  ₹
                </span>

              </div>

              <span className="text-sm font-bold text-emerald-400">
                FinSaathi AI
              </span>

              <span className="text-xs text-white/40">
                Human Support
              </span>

            </div>


            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">

              Human{' '}

              <span className="text-emerald-400">
                Support
              </span>

            </h1>


            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/50 sm:text-base">
              Review and resolve support requests
              escalated by FinSaathi AI.
            </p>

          </div>


          {/* Right side */}

          <div className="flex items-center gap-3">

            <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-[#11151c] px-4 py-2 text-xs font-semibold text-white/50 sm:flex">

              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]" />

              Support Center

            </div>


            <button
              onClick={loadEscalations}
              className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-5 py-2.5 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-400/20"
            >
              ↻ Refresh
            </button>

          </div>

        </header>


        {/* ================================================= */}
        {/* STATS */}
        {/* ================================================= */}

        {!loading && !error && (

          <div className="mb-8 grid gap-4 sm:grid-cols-3">

            <div className="rounded-2xl border border-white/10 bg-[#0c1016]/80 p-5 backdrop-blur-xl">

              <p className="text-xs uppercase tracking-widest text-white/40">
                Total Requests
              </p>

              <p className="mt-2 text-3xl font-bold">
                {escalations.length}
              </p>

            </div>


            <div className="rounded-2xl border border-red-400/10 bg-[#0c1016]/80 p-5 backdrop-blur-xl">

              <p className="text-xs uppercase tracking-widest text-white/40">
                Open
              </p>

              <p className="mt-2 text-3xl font-bold text-red-300">
                {
                  escalations.filter(
                    (item) =>
                      item.status === 'OPEN'
                  ).length
                }
              </p>

            </div>


            <div className="rounded-2xl border border-emerald-400/10 bg-[#0c1016]/80 p-5 backdrop-blur-xl">

              <p className="text-xs uppercase tracking-widest text-white/40">
                Resolved
              </p>

              <p className="mt-2 text-3xl font-bold text-emerald-300">
                {
                  escalations.filter(
                    (item) =>
                      item.status === 'RESOLVED'
                  ).length
                }
              </p>

            </div>

          </div>

        )}


        {/* ================================================= */}
        {/* ERROR */}
        {/* ================================================= */}

        {error && (

          <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/5 p-5 text-sm text-red-300">

            <div className="flex items-start gap-3">

              <span className="mt-0.5 text-lg">
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


        {/* ================================================= */}
        {/* LOADING */}
        {/* ================================================= */}

        {loading && (

          <div className="rounded-3xl border border-white/10 bg-[#0c1016]/80 p-16 text-center backdrop-blur-xl">

            <div className="mx-auto mb-5 h-10 w-10 animate-spin rounded-full border-2 border-white/10 border-t-emerald-400" />

            <p className="text-sm text-white/50">
              Loading support requests...
            </p>

          </div>

        )}


        {/* ================================================= */}
        {/* EMPTY */}
        {/* ================================================= */}

        {!loading &&
          !error &&
          escalations.length === 0 && (

            <div className="rounded-3xl border border-white/10 bg-[#0c1016]/80 p-16 text-center backdrop-blur-xl">

              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-2xl text-emerald-400">
                ✓
              </div>

              <h2 className="mt-5 text-xl font-bold">
                No Support Requests
              </h2>

              <p className="mt-2 text-sm text-white/40">
                There are currently no human
                support escalations.
              </p>

            </div>

          )}


        {/* ================================================= */}
        {/* ESCALATION CARDS */}
        {/* ================================================= */}

        {!loading &&
          escalations.length > 0 && (

            <div className="space-y-5">

              {escalations.map(
                (escalation) => {

                  const status =
                    statusStyle(
                      escalation.status
                    );

                  return (

                    <article
                      key={
                        escalation.request_id
                      }
                      className="group rounded-3xl border border-white/10 bg-[#0b0f15]/90 p-6 shadow-2xl backdrop-blur-xl transition duration-300 hover:border-emerald-400/20 hover:shadow-emerald-400/5 sm:p-7"
                    >

                      {/* TOP ROW */}

                      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">

                        <div>

                          <div className="flex flex-wrap items-center gap-3">

                            <h2 className="text-2xl font-bold tracking-tight">
                              {
                                escalation.request_id
                              }
                            </h2>


                            {/* STATUS */}

                            <span
                              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold ${status.badge}`}
                            >

                              <span
                                className={`h-1.5 w-1.5 rounded-full ${status.dot}`}
                              />

                              {
                                escalation.status
                              }

                            </span>


                            {/* URGENCY */}

                            <span
                              className={`rounded-full border px-3 py-1 text-xs font-bold ${urgencyStyle(
                                escalation.urgency
                              )}`}
                            >
                              {escalation.urgency}
                            </span>

                          </div>


                          <p className="mt-2 text-xs text-white/35">
                            Reference ID •{' '}
                            {
                              escalation.request_id
                            }
                          </p>

                        </div>


                        <div className="text-left lg:text-right">

                          <p className="text-xs uppercase tracking-wider text-white/30">
                            Created
                          </p>

                          <p className="mt-1 text-sm text-white/60">
                            {new Date(
                              escalation.created_at
                            ).toLocaleString()}
                          </p>

                        </div>

                      </div>


                      {/* USER */}

                      <div className="mt-6 flex items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.025] px-4 py-3">

                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-400/10 text-emerald-400">
                          👤
                        </div>

                        <div>

                          <p className="text-[10px] uppercase tracking-widest text-white/30">
                            Caller
                          </p>

                          <p className="mt-0.5 text-sm font-medium text-white/80">
                            {
                              escalation.user_id
                            }
                          </p>

                        </div>

                      </div>


                      {/* INFORMATION GRID */}

                      <div className="mt-6 grid gap-5 md:grid-cols-2">

                        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">

                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">
                            Reason
                          </p>

                          <p className="mt-2 font-semibold text-white">
                            {escalation.reason.replace(
                              /_/g,
                              ' '
                            )}
                          </p>

                        </div>


                        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">

                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">
                            Preferred Follow-up
                          </p>

                          <p className="mt-2 font-semibold text-white">
                            {
                              escalation.preferred_followup ||
                              'Not specified'
                            }
                          </p>

                        </div>

                      </div>


                      {/* SUMMARY */}

                      <div className="mt-5 rounded-2xl border border-emerald-400/10 bg-emerald-400/[0.025] p-5">

                        <div className="flex items-center gap-2">

                          <span className="text-emerald-400">
                            ✦
                          </span>

                          <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400/70">
                            AI Summary
                          </p>

                        </div>

                        <p className="mt-3 text-sm leading-7 text-white/70">
                          {
                            escalation.summary
                          }
                        </p>

                      </div>


                      {/* WHAT AI CHECKED */}

                      {escalation.what_checked && (

                        <div className="mt-5">

                          <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">
                            What AI Checked
                          </p>

                          <p className="mt-2 text-sm leading-6 text-white/45">
                            {
                              escalation.what_checked
                            }
                          </p>

                        </div>

                      )}


                      {/* RESOLUTION */}

                      {escalation.resolution && (

                        <div className="mt-5 rounded-2xl border border-emerald-400/20 bg-emerald-400/[0.04] p-5">

                          <div className="flex items-center gap-2">

                            <span className="text-emerald-400">
                              ✓
                            </span>

                            <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">
                              Resolution
                            </p>

                          </div>

                          <p className="mt-3 text-sm leading-6 text-emerald-100/70">
                            {
                              escalation.resolution
                            }
                          </p>

                        </div>

                      )}


                      {/* ACTIONS */}

                      <div className="mt-7 flex flex-col gap-3 border-t border-white/5 pt-6 sm:flex-row sm:justify-end">

                        {escalation.status ===
                          'OPEN' && (

                          <button
                            disabled={
                              updating ===
                              escalation.request_id
                            }
                            onClick={() =>
                              updateStatus(
                                escalation.request_id,
                                'IN_PROGRESS'
                              )
                            }
                            className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-6 py-3 text-sm font-bold text-emerald-300 transition hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            {updating ===
                            escalation.request_id
                              ? 'Updating...'
                              : 'Take Request →'}
                          </button>

                        )}


                        {escalation.status ===
                          'IN_PROGRESS' && (

                          <button
                            disabled={
                              updating ===
                              escalation.request_id
                            }
                            onClick={() =>
                              updateStatus(
                                escalation.request_id,
                                'RESOLVED'
                              )
                            }
                            className="rounded-xl bg-emerald-400 px-6 py-3 text-sm font-bold text-black shadow-[0_0_25px_rgba(52,211,153,0.18)] transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            {updating ===
                            escalation.request_id
                              ? 'Resolving...'
                              : 'Resolve Request ✓'}
                          </button>

                        )}


                        {escalation.status ===
                          'RESOLVED' && (

                          <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/5 px-5 py-3 text-sm font-semibold text-emerald-300">

                            <span>
                              ✓
                            </span>

                            Request Resolved

                          </div>

                        )}

                      </div>

                    </article>

                  );
                }
              )}

            </div>

          )}

      </div>

    </main>
  );
}
