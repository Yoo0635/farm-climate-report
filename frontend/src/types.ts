export interface PreviewRequest {
  region: string
  crop: string
  stage: string
  date_range_override?: string | null
}

export interface PreviewResponse {
  detailed_report: string
  refined_report: string
  sms_body: string
}

export interface BriefRequest {
  phone: string
  region: string
  crop: string
  stage: string
}

export interface BriefResponse {
  brief_id: string
  message_preview: string
}
