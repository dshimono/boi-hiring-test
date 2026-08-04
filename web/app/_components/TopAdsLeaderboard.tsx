import { formatNumber } from "../format";
import type { RankedAd } from "../types";

function formatMetricValue(metric: string, value: number): string {
  if (metric === "ctr" || metric === "engagement_rate") return `${value}%`;
  return formatNumber(value);
}

export default function TopAdsLeaderboard({ ads, metric }: { ads: RankedAd[]; metric: string }) {
  const maxValue = Math.max(...ads.map((a) => a.value), 0.0001);

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 sm:p-6">
      <ol className="flex flex-col gap-1">
        {ads.map((ad, i) => (
          <li
            key={ad.ad_id}
            className="grid grid-cols-[1.75rem_1fr_auto] items-center gap-4 rounded-lg px-2 py-2.5 transition-colors hover:bg-[var(--surface-2)]"
          >
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                i === 0
                  ? "bg-[var(--series-google)] text-white"
                  : "border border-[var(--border-strong)] text-[var(--text-secondary)]"
              }`}
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {i + 1}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{ad.title}</p>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--gridline)]">
                <div
                  className="h-full rounded-full bg-[var(--series-google)] transition-[width] duration-500 ease-out"
                  style={{ width: `${Math.max((ad.value / maxValue) * 100, 4)}%` }}
                />
              </div>
            </div>
            <span
              className="text-sm font-semibold tabular-nums"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {formatMetricValue(metric, ad.value)}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
