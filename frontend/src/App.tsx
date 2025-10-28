import { useEffect, useMemo, useState } from 'react'
import type { PreviewRequest, PreviewResponse, BriefRequest, BriefResponse } from './types'
import { normalizePhone, isValidE164 } from './phone'

const API_BASE = (import.meta as any).env?.VITE_API_BASE || ''

type FormState = {
  phone: string
  region: string
  crop: string
  stage: string
  scenario?: string
}

const LS_KEY = 'fcr:console:form'

export default function App() {
  const [form, setForm] = useState<FormState>({
    phone: '',
    region: 'KR/Seoul',
    crop: 'Strawberry',
    stage: 'Flowering',
    scenario: 'HEATWAVE',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [sendResult, setSendResult] = useState<BriefResponse | null>(null)

  // 복원
  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (raw) setForm((s) => ({ ...s, ...JSON.parse(raw) }))
    } catch {}
  }, [])

  // 저장
  useEffect(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify(form)) } catch {}
  }, [form])

  const normPhone = useMemo(() => normalizePhone(form.phone), [form.phone])
  const phoneOk = isValidE164(normPhone)
  const requiredOk = Boolean(form.region && form.crop && form.stage)

  const disabledSend = !phoneOk || !requiredOk || loading
  const disabledPreview = !requiredOk || loading

  async function callPreview() {
    setLoading(true); setError(null); setPreview(null)
    try {
      const payload: PreviewRequest = {
        region: form.region,
        crop: form.crop,
        stage: form.stage,
        scenario: form.scenario || undefined,
      }
      const res = await fetch(`${API_BASE}/api/briefs/preview`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      const json = await res.json() as PreviewResponse
      setPreview(json)
    } catch (e: any) {
      setError(e?.message || String(e))
    } finally { setLoading(false) }
  }

  async function sendBrief() {
    setLoading(true); setError(null); setSendResult(null)
    try {
      const payload: BriefRequest = {
        phone: normPhone,
        region: form.region,
        crop: form.crop,
        stage: form.stage,
        scenario: form.scenario || undefined,
      }
      const res = await fetch(`${API_BASE}/api/briefs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      const json = await res.json() as BriefResponse
      setSendResult(json)
    } catch (e: any) {
      setError(e?.message || String(e))
    } finally { setLoading(false) }
  }

  return (
    <div className="container">
      <h1>운영자 콘솔(React)</h1>
      <p className="muted">사용자 정보를 입력해 프리뷰 또는 실제 발송을 실행합니다.</p>

      <div className="card" style={{ marginTop: '1rem' }}>
        <div className="row">
          <div>
            <label>전화번호(E.164)</label>
            <input
              value={form.phone}
              onChange={(e) => setForm((s) => ({ ...s, phone: e.target.value }))}
              placeholder="010-1234-5678 또는 +821012345678"
            />
            <div className="muted" style={{ marginTop: '.25rem', fontSize: '.85rem' }}>
              정규화: <code>{normPhone || '-'}</code> {phoneOk ? '' : '(형식 확인 필요)'}
            </div>
          </div>
          <div>
            <label>지역(region)</label>
            <input
              value={form.region}
              onChange={(e) => setForm((s) => ({ ...s, region: e.target.value }))}
              placeholder="KR/Seoul"
            />
          </div>
          <div>
            <label>작물(crop)</label>
            <input
              value={form.crop}
              onChange={(e) => setForm((s) => ({ ...s, crop: e.target.value }))}
              placeholder="Strawberry"
            />
          </div>
          <div>
            <label>생육 단계(stage)</label>
            <input
              value={form.stage}
              onChange={(e) => setForm((s) => ({ ...s, stage: e.target.value }))}
              placeholder="Flowering"
            />
          </div>
          <div>
            <label>시나리오(선택)</label>
            <input
              value={form.scenario || ''}
              onChange={(e) => setForm((s) => ({ ...s, scenario: e.target.value || undefined }))}
              placeholder="HEATWAVE / RAIN / WIND / LOW_TEMP"
            />
          </div>
        </div>
        <div style={{ marginTop: '0.75rem', display: 'flex', gap: '.5rem' }}>
          <button onClick={callPreview} disabled={disabledPreview}>
            {loading ? '요청 중…' : '프리뷰 요청'}
          </button>
          <button onClick={sendBrief} disabled={disabledSend}>
            {loading ? '발송 중…' : 'SMS 발송'}
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ marginTop: '1rem', border: '1px solid #fecaca' }}>
          <strong>에러</strong>
          <pre>{error}</pre>
        </div>
      )}

      {sendResult && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h2>발송 결과</h2>
          <div><b>brief_id:</b> {sendResult.brief_id}</div>
          <h3>메시지 프리뷰</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{sendResult.message_preview}</pre>
        </div>
      )}

      {preview && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h2>SMS 본문 프리뷰</h2>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{preview.sms_body}</pre>
          <h3>정제 보고서</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{preview.refined_report}</pre>
          <details style={{ marginTop: '0.5rem' }}>
            <summary>상세 보고서 · RAG 로그</summary>
            <h4>상세 보고서</h4>
            <pre style={{ whiteSpace: 'pre-wrap' }}>{preview.detailed_report}</pre>
            <h4>RAG Passages</h4>
            <pre>{JSON.stringify(preview.rag_passages, null, 2)}</pre>
            <h4>Web Findings</h4>
            <pre>{JSON.stringify(preview.web_findings, null, 2)}</pre>
          </details>
        </div>
      )}

      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>환경 변수</h2>
        <p className="muted">Vite 개발 서버를 사용할 때는 프록시가 /api를 FastAPI로 전달합니다.</p>
        <pre>{JSON.stringify({ API_BASE: API_BASE || '(relative /api)' }, null, 2)}</pre>
      </div>
    </div>
  )
}

