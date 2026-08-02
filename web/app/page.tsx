export const dynamic = "force-dynamic";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

type Ad = {
  ad_id: string;
  title: string;
  body: string | null;
  image_url: string | null;
};

type CoverageAd = {
  ad_id: string;
  title: string;
  platforms_by_week: string[][];
};

type Coverage = {
  weeks: string[];
  ads: CoverageAd[];
};

type WeeklySummary = {
  weeks: string[];
  metric: string;
  series: Record<string, number[]>;
};

type StatsOverview = {
  ads_count: number;
  platforms_count: number;
  weeks_count: number;
  metric_rows_count: number;
  comments_count: number;
};

const PLATFORM_ORDER = ["Google", "LinkedIn", "Meta"];
const PLATFORM_COLORS: Record<string, string> = {
  Google: "var(--series-google)",
  LinkedIn: "var(--series-linkedin)",
  Meta: "var(--series-meta)",
};

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

function formatWeek(dateStr: string): string {
  return new Date(`${dateStr}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function formatYear(dateStr: string): number {
  return new Date(`${dateStr}T00:00:00Z`).getUTCFullYear();
}

function formatCompact(n: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

function adPlatforms(coverage: Coverage, adId: string): string[] {
  const covAd = coverage.ads.find((a) => a.ad_id === adId);
  if (!covAd) return [];
  const present = new Set(covAd.platforms_by_week.flat());
  return PLATFORM_ORDER.filter((p) => present.has(p));
}

export default async function Home() {
  const [ads, coverage, weeklySummary, stats] = await Promise.all([
    getJSON<Ad[]>("/api/v1/ads"),
    getJSON<Coverage>("/api/v1/metrics/coverage"),
    getJSON<WeeklySummary>("/api/v1/metrics/weekly-summary"),
    getJSON<StatsOverview>("/api/v1/stats/overview"),
  ]);

  const dateRange =
    coverage.weeks.length > 0
      ? `${formatWeek(coverage.weeks[0])} – ${formatWeek(coverage.weeks[coverage.weeks.length - 1])}, ${formatYear(coverage.weeks[coverage.weeks.length - 1])}`
      : "";

  return (
    <main className="min-h-screen bg-[var(--surface-page)] text-[var(--text-primary)]">
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
          <div className="mt-6 overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
            <PlatformLegend />
            <CoverageHeatmap coverage={coverage} />
          </div>
        </section>

        <section className="mt-20 pb-24">
          <h2 className="text-xl font-semibold tracking-tight">Campaign creatives</h2>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            The {ads.length} ads behind the numbers above.
          </p>
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {ads.map((ad) => (
              <AdCard key={ad.ad_id} ad={ad} platforms={adPlatforms(coverage, ad.ad_id)} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
      <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value.toLocaleString("en-US")}</p>
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

function CoverageHeatmap({ coverage }: { coverage: Coverage }) {
  return (
    <table className="w-full border-collapse text-xs" style={{ tableLayout: "fixed" }}>
      <thead>
        <tr>
          <th className="w-44 py-1 pr-2 text-left font-medium text-[var(--text-secondary)]">Ad</th>
          {coverage.weeks.map((w) => (
            <th key={w} className="px-0.5 py-1 font-medium text-[var(--text-secondary)]">
              {formatWeek(w)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {coverage.ads.map((ad) => (
          <tr key={ad.ad_id} className="border-t border-[var(--border)]">
            <td className="py-1.5 pr-2 text-left">{ad.title}</td>
            {ad.platforms_by_week.map((platforms, i) => (
              <td key={i} className="px-0.5 py-1.5">
                <div className="flex items-center justify-center gap-0.5">
                  {platforms.length === 0 ? (
                    <span className="inline-block h-2.5 w-2.5 rounded-[2px] border border-[var(--border-strong)]" />
                  ) : (
                    platforms.map((p) => (
                      <span
                        key={p}
                        className="inline-block h-2.5 w-2.5 rounded-full"
                        style={{ background: PLATFORM_COLORS[p] }}
                      />
                    ))
                  )}
                </div>
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function AdCard({ ad, platforms }: { ad: Ad; platforms: string[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)]">
      {ad.image_url ? (
        <div className="flex aspect-square w-full items-center justify-center bg-[var(--surface-2)]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={ad.image_url} alt={ad.title} className="h-full w-full object-contain" />
        </div>
      ) : (
        <div className="flex aspect-square w-full items-center justify-center bg-[var(--surface-2)] text-xs text-[var(--text-muted)]">
          No image
        </div>
      )}
      <div className="p-4">
        <h3 className="text-sm font-medium leading-snug">{ad.title}</h3>
        {ad.body ? (
          <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-[var(--text-secondary)]">
            {ad.body}
          </p>
        ) : null}
        {platforms.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {platforms.map((p) => (
              <span key={p} className="flex items-center gap-1 text-[11px] text-[var(--text-secondary)]">
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{ background: PLATFORM_COLORS[p] }}
                />
                {p}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const residual = value / magnitude;
  const niceResidual = residual <= 1 ? 1 : residual <= 2 ? 2 : residual <= 5 ? 5 : 10;
  return niceResidual * magnitude;
}

function LineChart({ weeks, series }: { weeks: string[]; series: Record<string, number[]> }) {
  const width = 720;
  const height = 260;
  const marginLeft = 44;
  const marginRight = 56;
  const marginTop = 12;
  const marginBottom = 28;
  const plotWidth = width - marginLeft - marginRight;
  const plotHeight = height - marginTop - marginBottom;

  const seriesNames = PLATFORM_ORDER.filter((p) => series[p]);
  const allValues = seriesNames.flatMap((name) => series[name] ?? []);
  const maxValue = niceMax(Math.max(...allValues, 0));

  const xFor = (i: number) =>
    marginLeft + (weeks.length > 1 ? (i / (weeks.length - 1)) * plotWidth : plotWidth / 2);
  const yFor = (v: number) => marginTop + plotHeight - (v / maxValue) * plotHeight;

  const yTickCount = 4;
  const gridValues = Array.from({ length: yTickCount + 1 }, (_, i) => (maxValue / yTickCount) * i);

  const endLabels = seriesNames
    .map((name) => {
      const values = series[name];
      const lastValue = values[values.length - 1] ?? 0;
      return { name, value: lastValue, naturalY: yFor(lastValue), y: yFor(lastValue) };
    })
    .sort((a, b) => a.naturalY - b.naturalY);

  const minGap = 14;
  for (let i = 1; i < endLabels.length; i++) {
    if (endLabels[i].y - endLabels[i - 1].y < minGap) {
      endLabels[i].y = endLabels[i - 1].y + minGap;
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-4 text-xs text-[var(--text-secondary)]">
        {seriesNames.map((name) => (
          <span key={name} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: PLATFORM_COLORS[name] }}
            />
            {name}
          </span>
        ))}
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label="Weekly impressions by platform">
        {gridValues.map((v, i) => (
          <line
            key={i}
            x1={marginLeft}
            x2={width - marginRight}
            y1={yFor(v)}
            y2={yFor(v)}
            stroke="var(--gridline)"
            strokeWidth={1}
          />
        ))}
        {gridValues.map((v, i) => (
          <text
            key={i}
            x={marginLeft - 8}
            y={yFor(v)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={10}
            fill="var(--text-muted)"
          >
            {formatCompact(v)}
          </text>
        ))}
        {weeks.map((w, i) => (
          <text
            key={w}
            x={xFor(i)}
            y={height - 8}
            textAnchor="middle"
            fontSize={10}
            fill="var(--text-muted)"
          >
            {formatWeek(w)}
          </text>
        ))}
        {seriesNames.map((name) => {
          const values = series[name];
          const points = values.map((v, i) => `${xFor(i)},${yFor(v)}`).join(" ");
          const lastIndex = values.length - 1;
          return (
            <g key={name}>
              <polyline
                points={points}
                fill="none"
                stroke={PLATFORM_COLORS[name]}
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              <circle
                cx={xFor(lastIndex)}
                cy={yFor(values[lastIndex])}
                r={4}
                fill={PLATFORM_COLORS[name]}
                stroke="var(--surface-1)"
                strokeWidth={2}
              />
            </g>
          );
        })}
        {endLabels.map((l) => (
          <g key={l.name}>
            {Math.abs(l.y - l.naturalY) > 1 ? (
              <line
                x1={width - marginRight + 2}
                x2={width - marginRight + 14}
                y1={l.naturalY}
                y2={l.y}
                stroke="var(--border-strong)"
                strokeWidth={1}
              />
            ) : null}
            <text
              x={width - marginRight + 16}
              y={l.y}
              dominantBaseline="middle"
              fontSize={10}
              fill="var(--text-secondary)"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {formatCompact(l.value)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
