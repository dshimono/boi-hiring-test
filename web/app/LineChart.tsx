"use client";

import { useState, type KeyboardEvent, type PointerEvent } from "react";
import { PLATFORM_COLORS, PLATFORM_ORDER } from "./constants";
import { formatCompact, formatDate } from "./format";

function niceMax(value: number): number {
  if (value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const residual = value / magnitude;
  const niceResidual = residual <= 1 ? 1 : residual <= 2 ? 2 : residual <= 5 ? 5 : 10;
  return niceResidual * magnitude;
}

const WIDTH = 720;
const HEIGHT = 260;
const MARGIN_LEFT = 44;
const MARGIN_RIGHT = 56;
const MARGIN_TOP = 12;
const MARGIN_BOTTOM = 28;
const PLOT_WIDTH = WIDTH - MARGIN_LEFT - MARGIN_RIGHT;
const PLOT_HEIGHT = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM;

export default function LineChart({
  weeks,
  series,
}: {
  weeks: string[];
  series: Record<string, number[]>;
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const seriesNames = PLATFORM_ORDER.filter((p) => series[p]);
  const allValues = seriesNames.flatMap((name) => series[name] ?? []);
  const maxValue = niceMax(Math.max(...allValues, 0));

  const xFor = (i: number) =>
    MARGIN_LEFT + (weeks.length > 1 ? (i / (weeks.length - 1)) * PLOT_WIDTH : PLOT_WIDTH / 2);
  const yFor = (v: number) => MARGIN_TOP + PLOT_HEIGHT - (v / maxValue) * PLOT_HEIGHT;

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

  function indexFromPointer(e: PointerEvent<SVGRectElement>): number {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = MARGIN_LEFT + ((e.clientX - rect.left) / rect.width) * PLOT_WIDTH;
    const distances = weeks.map((_, i) => Math.abs(xFor(i) - x));
    return distances.indexOf(Math.min(...distances));
  }

  function onKeyDown(e: KeyboardEvent<SVGRectElement>): void {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      setHoverIndex((i) => Math.max((i ?? 0) - 1, 0));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setHoverIndex((i) => Math.min((i ?? -1) + 1, weeks.length - 1));
    } else if (e.key === "Escape") {
      setHoverIndex(null);
    }
  }

  const tooltipLeftPct = hoverIndex !== null ? (xFor(hoverIndex) / WIDTH) * 100 : 0;

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

      <div className="relative">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full"
          role="img"
          aria-label="Weekly impressions by platform"
        >
          {gridValues.map((v, i) => (
            <line
              key={i}
              x1={MARGIN_LEFT}
              x2={WIDTH - MARGIN_RIGHT}
              y1={yFor(v)}
              y2={yFor(v)}
              stroke="var(--gridline)"
              strokeWidth={1}
            />
          ))}
          {gridValues.map((v, i) => (
            <text
              key={i}
              x={MARGIN_LEFT - 8}
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
              y={HEIGHT - 8}
              textAnchor="middle"
              fontSize={10}
              fill="var(--text-muted)"
            >
              {formatDate(w)}
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
                  x1={WIDTH - MARGIN_RIGHT + 2}
                  x2={WIDTH - MARGIN_RIGHT + 14}
                  y1={l.naturalY}
                  y2={l.y}
                  stroke="var(--border-strong)"
                  strokeWidth={1}
                />
              ) : null}
              <text
                x={WIDTH - MARGIN_RIGHT + 16}
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

          {hoverIndex !== null ? (
            <>
              <line
                x1={xFor(hoverIndex)}
                x2={xFor(hoverIndex)}
                y1={MARGIN_TOP}
                y2={MARGIN_TOP + PLOT_HEIGHT}
                stroke="var(--border-strong)"
                strokeWidth={1}
              />
              {seriesNames.map((name) => (
                <circle
                  key={name}
                  cx={xFor(hoverIndex)}
                  cy={yFor(series[name][hoverIndex])}
                  r={5}
                  fill={PLATFORM_COLORS[name]}
                  stroke="var(--surface-1)"
                  strokeWidth={2}
                />
              ))}
            </>
          ) : null}

          <rect
            x={MARGIN_LEFT}
            y={MARGIN_TOP}
            width={PLOT_WIDTH}
            height={PLOT_HEIGHT}
            fill="transparent"
            tabIndex={0}
            role="slider"
            aria-label="Scrub weeks to read exact values"
            aria-valuemin={0}
            aria-valuemax={weeks.length - 1}
            aria-valuenow={hoverIndex ?? 0}
            aria-valuetext={hoverIndex !== null ? formatDate(weeks[hoverIndex]) : undefined}
            onPointerMove={(e) => setHoverIndex(indexFromPointer(e))}
            onPointerLeave={() => setHoverIndex(null)}
            onFocus={() => setHoverIndex((i) => i ?? 0)}
            onBlur={() => setHoverIndex(null)}
            onKeyDown={onKeyDown}
            style={{ cursor: "crosshair", outline: "none" }}
          />
        </svg>

        {hoverIndex !== null ? (
          <div
            className="pointer-events-none absolute top-0 flex -translate-x-1/2 flex-col gap-1 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs shadow-lg"
            style={{ left: `${Math.min(Math.max(tooltipLeftPct, 12), 88)}%` }}
          >
            <p className="font-medium text-[var(--text-primary)]">{formatDate(weeks[hoverIndex])}</p>
            {seriesNames.map((name) => (
              <div key={name} className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-2.5" style={{ background: PLATFORM_COLORS[name] }} />
                <span className="text-[var(--text-secondary)]">{name}</span>
                <span className="ml-auto font-semibold text-[var(--text-primary)]" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatCompact(series[name][hoverIndex])}
                </span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
