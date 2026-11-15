export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let message = `Request failed (${response.status})`;
  let code: string | undefined;
  try {
    const payload = await response.json();
    const detail = payload?.detail;
    if (typeof detail === 'string') message = detail;
    else if (detail?.message) message = detail.message;
    if (detail?.code) code = detail.code;
  } catch {
    // Keep the generic status message when the server does not return JSON.
  }
  return new ApiError(message, response.status, code);
}

const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;

async function requestWithTimeout(
  url: string,
  init: RequestInit,
  parentSignal?: AbortSignal,
  timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const forwardAbort = () => controller.abort(parentSignal?.reason);
  if (parentSignal?.aborted) forwardAbort();
  else parentSignal?.addEventListener('abort', forwardAbort, { once: true });

  const timeoutId = setTimeout(() => controller.abort('request_timeout'), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (parentSignal?.aborted) throw error;
    if (controller.signal.aborted) {
      throw new ApiError('The request timed out. Please try again.', 408, 'request_timeout');
    }
    throw new ApiError('Cannot reach the backend service. Check your connection and try again.', 0, 'network_error');
  } finally {
    clearTimeout(timeoutId);
    parentSignal?.removeEventListener('abort', forwardAbort);
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await requestWithTimeout(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  }, signal);
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await requestWithTimeout(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }, signal);
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<T>;
}

export type DashboardSummary = {
  data_status: 'available' | 'unavailable';
  dataset_catalog_count: number;
  raw_asset_count: number;
  scientifically_validated_asset_count: number;
  available_map_layer_count: number;
  validated_study_area_count: number;
  scientific_metrics: null;
  message: string | null;
};

export type TrendResponse = {
  data_status: 'available' | 'unavailable';
  indicator: string;
  study_area_id: string | null;
  series: Array<{ date: string; interval_end: string | null; value: number | null; units: string | null; valid_pixel_count: number | null; missing_pixel_count: number | null }>;
  trend_statistics: Array<{ result_type: string; value: number | null; unit: string | null; p_value: number | null; confidence_interval: Record<string, number> | null; sample_size: number | null }> | null;
  message?: string | null;
};

export type MapLayer = {
  id: string;
  indicator: string;
  variable: string;
  observation_mode: string | null;
  units: string | null;
  tile_service_url: string | null;
  status: string;
};

export type StorySummary = {
  data_status: string;
  period: { start: string; end: string; year: number };
  metrics: {
    evapotranspiration: { value: number; units: string; peak_month: number; peak_month_value_mm: number; point: { lat: number; lon: number }; status: string; interpretation: string };
    root_zone_soil_moisture: { value: number; units: string; minimum: number; minimum_date: string; maximum: number; maximum_date: string; point: { lat: number; lon: number }; status: string; interpretation: string };
    precipitation: { value: number; units: string; mean_rate: number; mean_rate_units: string; minimum_annualized_equivalent: number; maximum_annualized_equivalent: number; near_gldas_point_annualized_equivalent: number | null; grid_cells: number; grid_resolution: string; product_id: string; version: string; temporal_summary: string; calculation: string; status: string };
    noaa_temperature_reference: { value: number | null; units: string; source: string; available_days: number; last_available_date: string | null; status: string };
  };
  data_inventory: { gldas_daily_rows: number; gldas_days_with_eight_3h_steps: number; gpm_valid_grid_cells: number; noaa_station_count: number; noaa_alexandria_days: number; ndvi_available: boolean; lst_available: boolean };
  limitations: string[];
  qc: Record<string, number | boolean | null>;
};

export type StoryMonthlyResponse = {
  data_status: string;
  period: { start: string; end: string; frequency: string };
  series: Array<{
    month: number;
    evapotranspiration_mm: number | null;
    root_moisture_mean_kg_m2: number | null;
    root_moisture_month_min_kg_m2: number | null;
    root_moisture_month_max_kg_m2: number | null;
    noaa_alexandria_tavg_c_mean: number | null;
    noaa_alexandria_days: number;
  }>;
  interpretation: string;
};

export type PrecipitationGrid = {
  type: 'FeatureCollection';
  data_status: string;
  units: string;
  grid_resolution: string;
  cell_count: number;
  note: string;
  features: Array<{ type: 'Feature'; geometry: { type: 'Point'; coordinates: [number, number] }; properties: { precipitation_mean_rate_mm_hr: number; annualized_equivalent_mm_year: number; product_id: string; version: string; period: string; temporal_summary: string; status: string } }>;
};
