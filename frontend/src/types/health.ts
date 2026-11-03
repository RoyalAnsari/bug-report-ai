export interface HealthResponse {
  status: string
  models: {
    severity_loaded: boolean
    duplicates_loaded: boolean
  }
}
