export interface SettingsValues {
  review_margin: number
  duplicate_threshold: number
  duplicate_top_k: number
}

export interface ApplicationInfo {
  api_version: string
  cors_origins: string[]
  database: string
  models_loaded: { severity: boolean; duplicates: boolean }
}

export interface SettingsResponse {
  values: SettingsValues
  defaults: SettingsValues
  application: ApplicationInfo
  updated_at: string | null
}
