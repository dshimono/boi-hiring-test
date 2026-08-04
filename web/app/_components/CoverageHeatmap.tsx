"use client";

import { useRef, useState, type MouseEvent } from "react";
import { PLATFORM_COLORS } from "../constants";
import { formatDate } from "../format";
import type { Coverage } from "../types";

type Hover = {
  adIndex: number;
  weekIndex: number;
  x: number;
  y: number;
};

export default function CoverageHeatmap({ coverage }: { coverage: Coverage }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<Hover | null>(null);

  function updateHover(e: MouseEvent<HTMLTableCellElement>, adIndex: number, weekIndex: number) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHover({ adIndex, weekIndex, x: e.clientX - rect.left, y: e.clientY - rect.top });
  }

  const tooltipLeft = hover
    ? Math.min(Math.max(hover.x, 70), (containerRef.current?.clientWidth ?? 0) - 70)
    : 0;

  return (
    <div ref={containerRef} className="relative">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs" style={{ tableLayout: "fixed" }}>
          <thead>
            <tr>
              <th className="w-44 py-1 pr-2 text-left font-medium text-[var(--text-secondary)]">Ad</th>
              {coverage.weeks.map((w, weekIndex) => (
                <th
                  key={w}
                  className="px-0.5 py-1 font-medium transition-colors"
                  style={{
                    color: hover?.weekIndex === weekIndex ? "var(--text-primary)" : "var(--text-secondary)",
                  }}
                >
                  {formatDate(w)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {coverage.ads.map((ad, adIndex) => (
              <tr
                key={ad.ad_id}
                className="border-t border-[var(--border)] transition-colors"
                style={{ background: hover?.adIndex === adIndex ? "var(--border)" : undefined }}
              >
                <td className="py-1.5 pr-2 text-left">{ad.title}</td>
                {ad.platforms_by_week.map((platforms, weekIndex) => (
                  <td
                    key={weekIndex}
                    className="px-0.5 py-1.5"
                    onMouseEnter={(e) => updateHover(e, adIndex, weekIndex)}
                    onMouseMove={(e) => updateHover(e, adIndex, weekIndex)}
                    onMouseLeave={() => setHover(null)}
                  >
                    <div
                      className="flex items-center justify-center gap-0.5 rounded outline-offset-2"
                      style={{
                        outline:
                          hover?.adIndex === adIndex && hover?.weekIndex === weekIndex
                            ? "1.5px solid var(--border-strong)"
                            : "1.5px solid transparent",
                      }}
                    >
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
      </div>

      {hover ? (
        <div
          className="pointer-events-none absolute flex -translate-x-1/2 flex-col gap-1 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs shadow-lg"
          style={{ left: tooltipLeft, top: hover.y, transform: "translate(-50%, calc(-100% - 10px))" }}
        >
          <p className="font-medium text-[var(--text-primary)]">{formatDate(coverage.weeks[hover.weekIndex])}</p>
          {coverage.ads[hover.adIndex].platforms_by_week[hover.weekIndex].length === 0 ? (
            <p className="text-[var(--text-secondary)]">No data this week</p>
          ) : (
            coverage.ads[hover.adIndex].platforms_by_week[hover.weekIndex].map((p) => (
              <div key={p} className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full" style={{ background: PLATFORM_COLORS[p] }} />
                <span className="text-[var(--text-secondary)]">{p}</span>
              </div>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
