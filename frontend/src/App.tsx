import { useEffect, useMemo, useState } from "react";
import type {
  PreviewRequest,
  PreviewResponse,
  BriefRequest,
  BriefResponse,
} from "./types";
import { normalizePhone, isValidE164 } from "./phone";

const API_BASE = (import.meta as any).env?.VITE_API_BASE || "";

type FormState = {
  phone: string;
  region: string;
  crop: string;
  stage: string;
};

const LS_KEY = "fcr:console:form";
const REGIONS = ["수도권", "강원", "충청", "호남", "영남", "제주"] as const;

export default function App() {
  const [form, setForm] = useState<FormState>({
    phone: "",
    region: "수도권",
    crop: "딸기",
    stage: "발아기",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [sendResult, setSendResult] = useState<BriefResponse | null>(null);
  const [health, setHealth] = useState<"ok" | "error" | "pending">("pending");
  const [copied, setCopied] = useState<string | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);

  // 복원
  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) setForm((s) => ({ ...s, ...JSON.parse(raw) }));
    } catch {}
  }, []);

  // 저장
  useEffect(() => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(form));
    } catch {}
  }, [form]);

  // 헬스 체크
  useEffect(() => {
    let aborted = false;
    async function ping() {
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("bad status");
        const j = await res.json();
        if (!aborted) setHealth(j?.status === "ok" ? "ok" : "error");
      } catch {
        if (!aborted) setHealth("error");
      }
    }
    ping();
    const id = setInterval(ping, 15000);
    return () => {
      aborted = true;
      clearInterval(id);
    };
  }, []);

  const normPhone = useMemo(() => normalizePhone(form.phone), [form.phone]);
  const phoneOk = isValidE164(normPhone);
  const requiredOk = Boolean(form.region && form.crop && form.stage);

  const disabledSend = !phoneOk || !requiredOk || loading;
  const disabledPreview = !requiredOk || loading;

  async function callPreview() {
    setLoading(true);
    setError(null);
    setPreview(null);
    try {
      const payload: PreviewRequest = {
        region: form.region,
        crop: form.crop,
        stage: form.stage,
      };
      const res = await fetch(`${API_BASE}/api/briefs/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const json = (await res.json()) as PreviewResponse;
      setPreview(json);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  async function sendBrief() {
    setLoading(true);
    setError(null);
    setSendResult(null);
    try {
      const payload: BriefRequest = {
        phone: normPhone,
        region: form.region,
        crop: form.crop,
        stage: form.stage,
      };
      const res = await fetch(`${API_BASE}/api/briefs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      const json = (await res.json()) as BriefResponse;
      setSendResult(json);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  function copy(text: string, tag: string) {
    setCopyError(null);

    const copyLegacy = (t: string) => {
      try {
        const ta = document.createElement("textarea");
        ta.value = t;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.top = "-1000px";
        ta.style.left = "-1000px";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        return ok;
      } catch {
        return false;
      }
    };

    const cb: any = (navigator as any).clipboard;
    const secure = (window as any).isSecureContext;
    if (cb && secure) {
      cb.writeText(text)
        .then(() => {
          setCopied(tag);
          setTimeout(() => setCopied(null), 1200);
        })
        .catch(() => {
          const ok = copyLegacy(text);
          if (ok) {
            setCopied(tag);
            setTimeout(() => setCopied(null), 1200);
          } else {
            setCopyError(
              "클립보드 복사 실패: 브라우저 권한/보안 설정을 확인하세요."
            );
          }
        });
    } else {
      const ok = copyLegacy(text);
      if (ok) {
        setCopied(tag);
        setTimeout(() => setCopied(null), 1200);
      } else {
        setCopyError(
          "클립보드 복사 실패: 브라우저 권한/보안 설정을 확인하세요."
        );
      }
    }
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header-inner">
          <div className="brand">Farm Climate Reporter</div>
          <div style={{ display: "flex", gap: ".6rem", alignItems: "center" }}>
            <span className="muted" style={{ fontWeight: 600 }}>
              API
            </span>
            <span
              className={`badge ${
                health === "ok"
                  ? "ok"
                  : health === "pending"
                  ? "pending"
                  : "error"
              }`}
            >
              {health === "ok"
                ? "ok"
                : health === "pending"
                ? "확인 중"
                : "오류"}
            </span>
          </div>
        </div>
      </header>

      <main className="container">
        <h2 className="section-title">운영자 콘솔</h2>
        <p className="section-desc">
          사용자 정보를 입력해 프리뷰 또는 실제 발송을 실행합니다.
        </p>

        <section className="card" style={{ marginTop: "1rem" }}>
          <div className="grid grid-2">
            <div className="field">
              <label>전화번호(E.164)</label>
              <input
                value={form.phone}
                onChange={(e) =>
                  setForm((s) => ({ ...s, phone: e.target.value }))
                }
                placeholder="010-2216-8618 또는 +821022168618"
              />
              <div
                className="muted"
                style={{ marginTop: ".35rem", fontSize: ".85rem" }}
              >
                정규화:{" "}
                <span className="pill">
                  <code>{normPhone || "-"}</code>
                </span>{" "}
                {phoneOk ? "" : "(형식 확인 필요)"}
              </div>
            </div>
            <div className="field">
              <label>지역(권역)</label>
              <select
                value={form.region}
                onChange={(e) =>
                  setForm((s) => ({ ...s, region: e.target.value }))
                }
              >
                {REGIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>작물(crop)</label>
              <input
                value={form.crop}
                onChange={(e) =>
                  setForm((s) => ({ ...s, crop: e.target.value }))
                }
                placeholder="딸기"
              />
            </div>
            <div className="field">
              <label>생육 단계(stage)</label>
              <input
                value={form.stage}
                onChange={(e) =>
                  setForm((s) => ({ ...s, stage: e.target.value }))
                }
                placeholder="발아기"
              />
            </div>
            <div className="field">
              <label>시나리오</label>
              <input value="(legacy 제거됨)" disabled />
            </div>
          </div>
          <div className="toolbar" style={{ marginTop: ".9rem" }}>
            <button
              className="btn"
              onClick={callPreview}
              disabled={disabledPreview}
            >
              {loading ? "요청 중…" : "프리뷰 요청"}
            </button>
            <button
              className="btn btn-secondary"
              onClick={sendBrief}
              disabled={disabledSend}
            >
              {loading ? "발송 중…" : "SMS 발송"}
            </button>
          </div>
        </section>

        {error && (
          <section
            className="card"
            style={{ marginTop: "1rem", border: "1px solid #fecaca" }}
          >
            <strong>에러</strong>
            <pre>{error}</pre>
          </section>
        )}

        {copyError && (
          <section
            className="card"
            style={{ marginTop: "1rem", border: "1px solid #fecaca" }}
          >
            <strong>복사 오류</strong>
            <pre>{copyError}</pre>
          </section>
        )}

        {sendResult && (
          <section className="card" style={{ marginTop: "1rem" }}>
            <h3 style={{ marginTop: 0 }}>발송 결과</h3>
            <div
              style={{
                display: "flex",
                gap: ".5rem",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <b>brief_id:</b>
              <code>{sendResult.brief_id}</code>
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => copy(sendResult.brief_id, "brief_id")}
              >
                복사
              </button>
              {copied === "brief_id" && <span className="muted">복사됨</span>}
            </div>
            <h4>메시지 프리뷰</h4>
            <div
              style={{
                display: "flex",
                gap: ".5rem",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <button
                className="btn btn-ghost btn-icon"
                onClick={() => copy(sendResult.message_preview, "preview")}
              >
                복사
              </button>
              <span className="muted">
                길이:{" "}
                <span className="pill">
                  {sendResult.message_preview.length}
                </span>
              </span>
              {copied === "preview" && <span className="muted">복사됨</span>}
            </div>
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {sendResult.message_preview}
            </pre>
          </section>
        )}

        {preview && (
          <section className="card" style={{ marginTop: "1rem" }}>
            <h3 style={{ marginTop: 0 }}>SMS 본문 프리뷰</h3>
            <div
              style={{
                display: "flex",
                gap: ".5rem",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <span className="muted">
                길이: <span className="pill">{preview.sms_body.length}</span>
              </span>
            </div>
            <pre style={{ whiteSpace: "pre-wrap" }}>{preview.sms_body}</pre>
            <h4>정제 보고서</h4>
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {preview.refined_report}
            </pre>
            <details style={{ marginTop: "0.5rem" }}>
              <summary>상세 보고서</summary>
              <pre style={{ whiteSpace: "pre-wrap" }}>
                {preview.detailed_report}
              </pre>
            </details>
          </section>
        )}

        <section className="card" style={{ marginTop: "1rem" }}>
          <h3 style={{ marginTop: 0 }}>환경</h3>
          <p className="muted">
            Vite 개발 서버를 사용할 때는 프록시가 /api를 FastAPI로 전달합니다.
          </p>
          <pre>
            {JSON.stringify(
              { API_BASE: API_BASE || "(relative /api)" },
              null,
              2
            )}
          </pre>
        </section>

        <div className="footer">
          © {new Date().getFullYear()} Farm Climate Reporter
        </div>
      </main>
    </>
  );
}
