"use client";

import { useCallback, useEffect, useState } from "react";

type Project = {
  project_name: string;
  district: string;
  transaction_count: number;
  median_psf: number | null;
};

type YearStats = {
  transaction_count: number;
  median_psf: number | null;
  median_price: number | null;
};

type ProjectDetail = Project & {
  median_price: number | null;
  by_year: Record<string, YearStats>;
};

type Estimate = {
  project: string;
  estimated_price: number | null;
  psf_used: number | null;
  n_transactions: number;
  window?: { start: string; end: string };
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const META = process.env.NEXT_PUBLIC_API_URL ? "dev:3000→8000" : "same-origin";

const fmtInt = (n: number | null | undefined) =>
  n == null ? "—" : Math.round(n).toLocaleString();

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [detailYear, setDetailYear] = useState<string>("all");
  const [year, setYear] = useState<string>("2025");
  const [area, setArea] = useState<string>("1000");
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJSON<Project[]>("/projects")
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, []);

  const loadDetail = useCallback(
    async (name: string) => {
      try {
        const q = detailYear === "all" ? "" : `?year=${detailYear}`;
        setDetail(await getJSON<ProjectDetail>(`/projects/${encodeURIComponent(name)}${q}`));
      } catch (e) {
        setError(String(e));
      }
    },
    [detailYear],
  );

  useEffect(() => {
    if (selected) void loadDetail(selected);
  }, [selected, loadDetail]);

  const runEstimate = useCallback(async () => {
    if (!selected) return;
    try {
      setEstimate(
        await getJSON<Estimate>(
          `/estimate?project=${encodeURIComponent(selected)}&area_sqft=${encodeURIComponent(area)}`,
        ),
      );
    } catch (e) {
      setError(String(e));
    }
  }, [selected, area]);

  const years = detail ? Object.keys(detail.by_year).sort().reverse() : [];
  const activeDetail =
    detail && detailYear === "all"
      ? detail
      : detail && detailYear !== "all"
        ? { ...detail, ...detail.by_year[detailYear] }
        : null;

  return (
    <main className="mx-auto flex h-screen max-w-6xl flex-col overflow-hidden px-4 py-6 sm:px-6">
      <header className="entrance">
        <div className="label">Data · 1,603 clean rows · {META}</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
          Property Transactions
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--g500)]">
          Singapore condo resale summaries computed from a cleaned transactions
          dataset, served by the same process that renders this page.
        </p>
      </header>

      <div className="entrance entrance-1 mt-5 grid min-h-0 flex-1 gap-6 lg:grid-cols-2">
        <section className="flex min-h-0 flex-col">
          <div className="label">01 — Projects</div>
          <div className="card mt-2 min-h-0 flex-1 overflow-y-auto">
            <table className="w-full min-w-[520px] border-collapse text-sm">
              <thead className="sticky top-0 bg-[color:var(--g50)]">
                <tr className="label text-left">
                  <th className="px-4 py-3 font-normal">Project</th>
                  <th className="px-4 py-3 font-normal">District</th>
                  <th className="px-4 py-3 text-right font-normal">Median PSF</th>
                  <th className="px-4 py-3 text-right font-normal">Transactions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p, i) => (
                  <tr
                    key={p.project_name}
                    className={`cursor-pointer border-t transition-colors hover:bg-[color:var(--g100)] ${
                      selected === p.project_name ? "bg-[color:var(--g100)]" : ""
                    }`}
                    onClick={() => setSelected(p.project_name)}
                  >
                    <td className="px-4 py-2.5 font-medium">{p.project_name}</td>
                    <td className="mono px-4 py-2.5 text-xs text-[color:var(--g500)]">
                      {p.district}
                    </td>
                    <td className="mono px-4 py-2.5 text-right text-xs">
                      {fmtInt(p.median_psf)}
                    </td>
                    <td className="mono px-4 py-2.5 text-right text-xs">
                      {fmtInt(p.transaction_count)}
                    </td>
                  </tr>
                ))}
                {!loading && projects.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-sm text-[color:var(--g500)]">
                      No projects.
                    </td>
                  </tr>
                )}
                {loading && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-sm text-[color:var(--g500)]">
                      Loading…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <div className="flex min-h-0 flex-col gap-6 overflow-y-auto">
          <section>
            <div className="label">02 — Detail</div>
          <div className="card mt-3 p-5">
            {!selected && (
              <p className="text-sm text-[color:var(--g500)]">Select a project.</p>
            )}
            {activeDetail && (
              <>
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <h2 className="text-xl font-semibold tracking-tight">
                    {activeDetail.project_name}
                  </h2>
                  <div className="flex items-center gap-2">
                    <label className="label" htmlFor="year">
                      Year
                    </label>
                    <select
                      id="year"
                      value={detailYear}
                      onChange={(e) => setDetailYear(e.target.value)}
                    >
                      <option value="all">All</option>
                      {years.map((y) => (
                        <option key={y} value={y}>
                          {y}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-[color:var(--g200)] bg-[color:var(--g200)]">
                  <Stat label="Median PSF" value={fmtInt(activeDetail.median_psf)} />
                  <Stat label="Median Price" value={`S$${fmtInt(activeDetail.median_price)}`} />
                  <Stat label="Count" value={fmtInt(activeDetail.transaction_count)} />
                </div>
                <div className="mono label mt-5">By year — median psf</div>
                <div className="mt-2 space-y-1">
                  {years.map((y) => {
                    const s = detail?.by_year[y];
                    const max = Math.max(
                      1,
                      ...Object.values(detail?.by_year ?? {}).map((v) => v.median_psf ?? 0),
                    );
                    const pct = s?.median_psf ? (s.median_psf / max) * 100 : 0;
                    return (
                      <button
                        key={y}
                        className="block w-full text-left"
                        onClick={() => setDetailYear(y)}
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="mono text-[color:var(--g500)]">{y}</span>
                          <span className="mono">{fmtInt(s?.median_psf)}</span>
                        </div>
                        <div className="hairline mt-1 h-1 w-full bg-[color:var(--g100)]">
                          <div
                            className="h-1 bg-[color:var(--ink)]"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </section>

        <section>
          <div className="label">03 — Estimate</div>
          <div className="card mt-3 p-5">
            {!selected && (
              <p className="text-sm text-[color:var(--g500)]">Select a project first.</p>
            )}
            {selected && (
              <>
                <div className="space-y-4">
                  <div>
                    <label className="label" htmlFor="area">
                      Area (sqft)
                    </label>
                    <input
                      id="area"
                      type="number"
                      min="1"
                      value={area}
                      onChange={(e) => setArea(e.target.value)}
                      className="mt-1 w-full"
                    />
                  </div>
                  <button
                    onClick={runEstimate}
                    className="w-full rounded-md bg-[color:var(--ink)] py-2.5 text-sm font-medium text-[color:var(--bg)] transition-opacity hover:opacity-85"
                  >
                    Estimate price
                  </button>
                </div>
                {estimate && (
                  <div className="mt-5 space-y-3 border-t border-[color:var(--g200)] pt-4">
                    <div className="flex items-baseline justify-between">
                      <span className="label">Estimated price</span>
                      <span className="text-lg font-semibold">
                        {estimate.estimated_price == null
                          ? "—"
                          : `S$${fmtInt(estimate.estimated_price)}`}
                      </span>
                    </div>
                    <div className="flex items-baseline justify-between">
                      <span className="label">PSF used</span>
                      <span className="mono text-sm">{fmtInt(estimate.psf_used)}</span>
                    </div>
                    <div className="flex items-baseline justify-between">
                      <span className="label">Transactions</span>
                      <span className="mono text-sm">{estimate.n_transactions}</span>
                    </div>
                    {estimate.window && (
                      <p className="mono text-[10px] leading-relaxed text-[color:var(--g400)]">
                        trailing 12 mo · {estimate.window.start} → {estimate.window.end}
                      </p>
                    )}
                  </div>
                )}
                <p className="mono mt-4 text-[10px] leading-relaxed text-[color:var(--g400)]">
                  Naive estimate: median psf × area. No bedrooms, floor, time
                  decay, or comparables.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
      </div>

      {error && (
        <footer className="entrance entrance-3 hairline mt-4 pt-3">
          <p className="mono text-xs text-[color:var(--g500)]">
            {error} — is the API running on the same origin?
          </p>
        </footer>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[color:var(--bg)] px-4 py-3">
      <div className="label">{label}</div>
      <div className="mono mt-1 text-sm">{value}</div>
    </div>
  );
}