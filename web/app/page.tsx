import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import AdCardsGrid from "./_components/AdCardsGrid";
import ChatBox from "./_components/ChatBox";
import CoverageHeatmap from "./_components/CoverageHeatmap";
import Header from "./_components/Header";
import LineChart from "./_components/LineChart";
import TopAdsLeaderboard from "./_components/TopAdsLeaderboard";
import { PLATFORM_COLORS, PLATFORM_ORDER } from "./constants";
import { formatNumber, formatDate, formatYear } from "./format";
import type { Ad, AdDetail, Coverage, RankAdsResponse, StatsOverview, WeeklySummary } from "./types";

export const dynamic = "force-dynamic";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

async function getJSON<T>(path: string, token: string | undefined): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (res.status === 401) {
    redirect("/sign-in");
  }
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export default async function Home() {
  const token = cookies().get("access_token")?.value;

  const [ads, coverage, weeklySummary, stats, topAds] = await Promise.all([
    getJSON<Ad[]>("/api/v1/ads", token),
    getJSON<Coverage>("/api/v1/metrics/coverage", token),
    getJSON<WeeklySummary>("/api/v1/metrics/weekly-summary", token),
    getJSON<StatsOverview>("/api/v1/stats/overview", token),
    getJSON<RankAdsResponse>("/api/v1/metrics/ranked?top_n=5", token),
  ]);

  const adDetails = await Promise.all(
    ads.map((ad) => getJSON<AdDetail>(`/api/v1/ads/${ad.ad_id}`, token))
  );

  const dateRange =
    coverage.weeks.length > 0
      ? `${formatDate(coverage.weeks[0])} – ${formatDate(coverage.weeks[coverage.weeks.length - 1])}, ${formatYear(coverage.weeks[coverage.weeks.length - 1])}`
      : "";

  return (
    <main className="min-h-screen bg-[var(--surface-page)] text-[var(--text-primary)]">
      <Header />
      <div className="mx-auto max-w-5xl px-6 py-16 sm:px-8 sm:py-24">
        <p className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--text-muted)]">
          Board of Innovation &middot; Ad performance
        </p>

        <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.1] tracking-tight sm:text-5xl">
          Autonomous ad performance, at a glance.
        </h1>

        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[var(--text-secondary)]">
          {stats.ads_count} creatives running across {stats.platforms_count} platforms, tracked weekly
          {dateRange ? ` from ${dateRange}` : ""}.
        </p>

        <div className="mt-12 grid grid-cols-2 gap-3 sm:grid-cols-5">
          <StatTile label="Ads" value={stats.ads_count} />
          <StatTile label="Platforms" value={stats.platforms_count} />
          <StatTile label="Weeks tracked" value={stats.weeks_count} />
          <StatTile label="Metric rows" value={stats.metric_rows_count} />
          <StatTile label="Comments" value={stats.comments_count} />
        </div>

        <section className="mt-20">
          <h2 className="text-xl font-semibold tracking-tight">Chat with your data</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Ask questions about your ads and their performance.
          </p>
          <div className="mt-6">
            <ChatBox />
          </div>
        </section>

        <section className="mt-20">
          <h2 className="text-xl font-semibold tracking-tight">Top ads by CTR</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            The highest click-through-rate creatives.
          </p>
          <div className="mt-6">
            <TopAdsLeaderboard ads={topAds.ads} metric={topAds.metric} />
          </div>
        </section>

        <section className="mt-20">
          <h2 className="text-xl font-semibold tracking-tight">Weekly impressions by platform</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Total impressions per week, split by platform.
          </p>
          <div className="mt-6 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
            <LineChart weeks={weeklySummary.weeks} series={weeklySummary.series} />
          </div>
        </section>

        <section className="mt-20">
          <h2 className="text-xl font-semibold tracking-tight">Coverage by ad, platform, and week</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Which ads have metrics data on which platform, for each weekly snapshot. Empty cells mark
            weeks with no data for that ad at all.
          </p>
          <div className="mt-6 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
            <PlatformLegend />
            <CoverageHeatmap coverage={coverage} />
          </div>
        </section>

        <section className="mt-20 pb-24">
          <h2 className="text-xl font-semibold tracking-tight">Campaign creatives</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            The {ads.length} ads behind the numbers above. Click a card for the full detail view.
          </p>
          <AdCardsGrid ads={adDetails} />
        </section>
      </div>
    </main>
  );
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
      <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{formatNumber(value)}</p>
    </div>
  );
}

function PlatformLegend() {
  return (
    <div className="mb-4 flex flex-wrap gap-4 text-xs text-[var(--text-secondary)]">
      {PLATFORM_ORDER.map((p) => (
        <span key={p} className="flex items-center gap-1.5">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: PLATFORM_COLORS[p] }}
          />
          {p}
        </span>
      ))}
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-[2px] border border-[var(--border-strong)]" />
        No data that week
      </span>
    </div>
  );
}
