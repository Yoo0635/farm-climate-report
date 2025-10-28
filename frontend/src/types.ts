export interface PreviewRequest {
  region: string
  crop: string
  stage: string
  scenario?: string
  date_range_override?: string | null
}

export interface PreviewResponse {
  rag_passages: string[]
  web_findings: string[]
  detailed_report: string
  refined_report: string
  sms_body: string
}

export interface BriefRequest {
  phone: string
  region: string
  crop: string
  stage: string
  scenario?: string
}

export interface BriefResponse {
  brief_id: string
  message_preview: string
}

