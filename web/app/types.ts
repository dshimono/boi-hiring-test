export type Ad = {
  ad_id: string;
  title: string;
  body: string | null;
  image_url: string | null;
};

export type PlatformMetrics = {
  platform: string;
  impressions: number;
  clicks: number;
  engagements: number;
  ctr: number;
};

export type Comment = {
  date: string;
  platform: string;
  comment: string;
};

export type AdDetail = {
  ad_id: string;
  title: string;
  body: string | null;
  image_url: string | null;
  impressions: number;
  clicks: number;
  engagements: number;
  ctr: number;
  engagement_rate: number;
  platforms: PlatformMetrics[];
  comments: Comment[];
};

export type CoverageAd = {
  ad_id: string;
  title: string;
  platforms_by_week: string[][];
};

export type Coverage = {
  weeks: string[];
  ads: CoverageAd[];
};

export type WeeklySummary = {
  weeks: string[];
  metric: string;
  series: Record<string, number[]>;
};

export type StatsOverview = {
  ads_count: number;
  platforms_count: number;
  weeks_count: number;
  metric_rows_count: number;
  comments_count: number;
};
