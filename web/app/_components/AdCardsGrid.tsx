"use client";

import { useEffect, useState } from "react";
import { PLATFORM_COLORS } from "../constants";
import { formatDate, formatNumber } from "../format";
import type { AdDetail } from "../types";

export default function AdCardsGrid({ ads }: { ads: AdDetail[] }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const openAd = ads.find((a) => a.ad_id === openId) ?? null;

  useEffect(() => {
    if (!openId) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenId(null);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [openId]);

  return (
    <>
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {ads.map((ad) => (
          <button
            key={ad.ad_id}
            type="button"
            onClick={() => setOpenId(ad.ad_id)}
            className="group w-full appearance-none overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-left transition-all duration-300 ease-out hover:-translate-y-1 hover:border-[var(--border-strong)] hover:shadow-[0_16px_32px_-16px_rgba(0,0,0,0.28)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--border-strong)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
          >
            <AdThumb ad={ad} />
            <div className="p-4">
              <h3 className="text-sm font-medium leading-snug">{ad.title}</h3>
              {ad.body ? (
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-[var(--text-secondary)]">
                  {ad.body}
                </p>
              ) : null}
              <div className="mt-3 flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                <span>
                  Impressions{" "}
                  <b className="font-semibold text-[var(--text-primary)]">{formatNumber(ad.impressions)}</b>
                </span>
                <span>
                  CTR <b className="font-semibold text-[var(--text-primary)]">{ad.ctr}%</b>
                </span>
                {ad.platforms.length > 0 ? (
                  <span className="flex items-center gap-1">
                    {ad.platforms.map((p) => (
                      <span
                        key={p.platform}
                        title={p.platform}
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ background: PLATFORM_COLORS[p.platform] }}
                      />
                    ))}
                  </span>
                ) : null}
              </div>
              <span
                className="mt-3 flex items-center gap-1 text-xs font-medium group-hover:underline"
                style={{ color: "var(--series-google)" }}
              >
                See details
                <span className="transition-transform group-hover:translate-x-0.5">&rarr;</span>
              </span>
            </div>
          </button>
        ))}
      </div>

      {openAd ? <AdModal ad={openAd} onClose={() => setOpenId(null)} /> : null}
    </>
  );
}

function AdThumb({ ad }: { ad: AdDetail }) {
  return ad.image_url ? (
    <div className="flex aspect-square w-full items-center justify-center bg-[var(--surface-2)]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ad.image_url}
        alt={ad.title}
        className="h-full w-full object-contain transition-transform duration-300 ease-out group-hover:scale-[1.04] motion-reduce:group-hover:scale-100"
      />
    </div>
  ) : (
    <div className="flex aspect-square w-full items-center justify-center bg-[var(--surface-2)] text-xs text-[var(--text-muted)]">
      No image
    </div>
  );
}

function AdModal({ ad, onClose }: { ad: AdDetail; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-6"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="max-h-[88vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-[var(--surface-1)]">
        <div className="relative flex aspect-[16/9] w-full items-center justify-center bg-[var(--surface-2)]">
          {ad.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={ad.image_url} alt={ad.title} className="h-full w-full object-contain" />
          ) : null}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface-1)] text-[var(--text-primary)] shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--border-strong)]"
          >
            &times;
          </button>
        </div>

        <div className="p-6">
          <h3 className="text-lg font-semibold">{ad.title}</h3>
          {ad.body ? (
            <p className="mt-1.5 text-sm leading-relaxed text-[var(--text-secondary)]">{ad.body}</p>
          ) : null}

          <div className="mt-5 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            <Kpi label="Impressions" value={formatNumber(ad.impressions)} />
            <Kpi label="Clicks" value={formatNumber(ad.clicks)} />
            <Kpi label="CTR" value={`${ad.ctr}%`} />
            <Kpi label="Engagement rate" value={`${ad.engagement_rate}%`} />
          </div>

          <p className="mb-2.5 mt-6 text-xs font-semibold">Performance by platform</p>
          {ad.platforms.length > 0 ? (
            <table className="mb-6 w-full border-collapse text-sm">
              <thead>
                <tr>
                  <th className="border-b border-[var(--border)] px-2 py-1.5 text-left text-xs font-medium text-[var(--text-secondary)]">
                    Platform
                  </th>
                  <th className="border-b border-[var(--border)] px-2 py-1.5 text-left text-xs font-medium text-[var(--text-secondary)]">
                    Impressions
                  </th>
                  <th className="border-b border-[var(--border)] px-2 py-1.5 text-left text-xs font-medium text-[var(--text-secondary)]">
                    Clicks
                  </th>
                  <th className="border-b border-[var(--border)] px-2 py-1.5 text-left text-xs font-medium text-[var(--text-secondary)]">
                    CTR
                  </th>
                </tr>
              </thead>
              <tbody>
                {ad.platforms.map((p) => (
                  <tr key={p.platform}>
                    <td className="border-b border-[var(--border)] px-2 py-1.5">
                      <span className="flex items-center gap-1.5">
                        <span
                          className="inline-block h-2 w-2 rounded-full"
                          style={{ background: PLATFORM_COLORS[p.platform] }}
                        />
                        {p.platform}
                      </span>
                    </td>
                    <td
                      className="border-b border-[var(--border)] px-2 py-1.5"
                      style={{ fontVariantNumeric: "tabular-nums" }}
                    >
                      {formatNumber(p.impressions)}
                    </td>
                    <td
                      className="border-b border-[var(--border)] px-2 py-1.5"
                      style={{ fontVariantNumeric: "tabular-nums" }}
                    >
                      {formatNumber(p.clicks)}
                    </td>
                    <td
                      className="border-b border-[var(--border)] px-2 py-1.5"
                      style={{ fontVariantNumeric: "tabular-nums" }}
                    >
                      {p.ctr}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="mb-6 text-sm text-[var(--text-muted)]">No platform data for this ad.</p>
          )}

          <p className="mb-2.5 text-xs font-semibold">Recent comments</p>
          {ad.comments.length > 0 ? (
            <div className="flex max-h-48 flex-col gap-2 overflow-y-auto">
              {ad.comments.map((c, i) => (
                <div
                  key={i}
                  className="flex items-start justify-between gap-3 rounded-lg bg-[var(--surface-2)] px-3 py-2 text-sm"
                >
                  <span className="flex items-start gap-2">
                    <span
                      title={c.platform}
                      className="mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full"
                      style={{ background: PLATFORM_COLORS[c.platform] }}
                    />
                    <span>{c.comment}</span>
                  </span>
                  <span
                    className="shrink-0 text-xs text-[var(--text-muted)]"
                    style={{ fontVariantNumeric: "tabular-nums" }}
                  >
                    {formatDate(c.date)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">No comments recorded for this ad yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-[var(--surface-2)] p-3">
      <p className="text-[11px] text-[var(--text-secondary)]">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
