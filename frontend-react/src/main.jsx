import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity, AlertCircle, ArrowDownRight, ArrowUpRight, CheckCircle2,
  ChevronDown, CircleHelp, ClipboardCheck, FileImage, FileText, FlaskConical,
  History, LayoutDashboard, LoaderCircle, MessageCircle, Moon, RefreshCw,
  ShieldCheck, Sparkles, Sun, UploadCloud, X, Globe, Mic, Download
} from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const fmt = (v) => v === null || v === undefined || v === "" ? "—" : String(v);
const safeDate = (v) => v ? String(v).slice(0, 10) : "Date not available";

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, options);
  let body;
  try { body = await res.json(); } catch { body = {}; }
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`);
  return body;
}

function App() {
  const [dark, setDark] = useState(false);
  const [tab, setTab] = useState("overview");
  const [file, setFile] = useState(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [activeReport, setActiveReport] = useState(null);
  const [reports, setReports] = useState([]);
  const [previousId, setPreviousId] = useState("");
  const [currentId, setCurrentId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState(null);
  const [chatReport, setChatReport] = useState("");
  const [biomarker, setBiomarker] = useState("");
  const [trend, setTrend] = useState(null);
  const [health, setHealth] = useState(null);
  const [advancedReport, setAdvancedReport] = useState("");
  const [language, setLanguage] = useState("Hindi");
  const [translated, setTranslated] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [review, setReview] = useState({ status: "pending", reviewer: "", note: "" });
  const [reviewBusy, setReviewBusy] = useState(false);

  async function refresh() {
    try {
      const [rs, h] = await Promise.all([api("/api/reports"), api("/api/health")]);
      setReports(rs); setHealth(h);
      if (!chatReport && rs.length) setChatReport(rs[0].report_id);
      if (!previousId && rs.length > 1) setPreviousId(rs[1].report_id);
      if (!currentId && rs.length) setCurrentId(rs[0].report_id);
      if (!advancedReport && rs.length) setAdvancedReport(rs[0].report_id);
    } catch (e) { setError(`Backend unavailable. Start FastAPI on port 8000. ${e.message}`); }
  }
  useEffect(() => { refresh(); }, []);

  const selectedAnalysis = analysis?.analysis || analysis;
  const resultCount = selectedAnalysis?.results?.length || 0;
  const flaggedCount = selectedAnalysis?.warnings?.length || 0;

  async function analyze() {
    if (!file) { setError("Choose a PDF or image first."); return; }
    setBusy(true); setError(""); setNotice(""); setAnalysis(null);
    const form = new FormData();
    form.append("file", file);
    form.append("consent_to_store", consent ? "true" : "false");
    try {
      const result = await api("/api/analyze", { method: "POST", body: form });
      setAnalysis(result); setActiveReport(result.report_id || null);
      setNotice(result.stored ? "Analysis complete and saved to local history." : "Analysis complete. This report was not saved.");
      if (result.report_id) await refresh();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function compare() {
    setError(""); setComparison(null);
    try {
      setComparison(await api("/api/compare", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ previous_report_id: previousId, current_report_id: currentId })
      }));
    } catch (e) { setError(e.message); }
  }

  async function ask() {
    setError(""); setChatAnswer(null);
    try {
      setChatAnswer(await api("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: chatReport, question })
      }));
    } catch (e) { setError(e.message); }
  }

  async function showTrend() {
    setError(""); setTrend(null);
    try {
      setTrend(await api(`/api/trends/${encodeURIComponent(chatReport)}?biomarker=${encodeURIComponent(biomarker)}`));
    } catch (e) { setError(e.message); }
  }

  const nav = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "analyze", label: "Analyze report", icon: UploadCloud },
    { id: "compare", label: "Compare reports", icon: Activity },
    { id: "assistant", label: "Report Q&A", icon: MessageCircle },
    { id: "history", label: "Report history", icon: History },
    { id: "advanced", label: "Review & evaluation", icon: ClipboardCheck },
  ];

  return <div className={dark ? "app dark" : "app"}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><FlaskConical size={22}/></div><div><b>Labwise</b><small>REPORT ANALYZER</small></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{nav.map(n => <button key={n.id} className={`nav-item ${tab === n.id ? "active" : ""}`} onClick={() => setTab(n.id)}><n.icon size={18}/><span>{n.label}</span>{n.id === "history" && <em>{reports.length}</em>}</button>)}</nav>
      <div className="sidebar-bottom">
        <div className="safety-mini"><ShieldCheck size={18}/><div><b>Safety first</b><small>Clinical review required</small></div></div>
        <button className="nav-item" onClick={() => setDark(!dark)}>{dark ? <Sun size={18}/> : <Moon size={18}/>}<span>{dark ? "Light theme" : "Dark theme"}</span></button>
        <div className="profile"><div className="avatar">LA</div><div><b>Local workspace</b><small>Private prototype</small></div><ChevronDown size={16}/></div>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div><div className="eyebrow">HEALTH DATA WORKSPACE </div><h1>{nav.find(n => n.id === tab)?.label || "Overview"}</h1></div>
        <div className="top-actions"><span className={`connection ${health?.status === "ok" ? "online" : ""}`}><span/> {health?.status === "ok" ? "API connected" : "Connecting…"}</span><button className="icon-btn" title="Refresh" onClick={refresh}><RefreshCw size={17}/></button></div>
      </header>

      {error && <div className="alert error"><AlertCircle size={18}/><span>{error}</span><button onClick={() => setError("")}><X size={16}/></button></div>}
      {notice && <div className="alert success"><CheckCircle2 size={18}/><span>{notice}</span><button onClick={() => setNotice("")}><X size={16}/></button></div>}

      {tab === "overview" && <section className="page">
        <div className="welcome"><div><div className="welcome-tag"><Sparkles size={14}/> SMART LAB WORKSPACE</div><h2>Understand your report.<br/><span>Keep the context.</span></h2><p>Extract lab values, review what was captured, and compare saved reports — with safety checks at every step.</p><button className="primary" onClick={() => setTab("analyze")}>Analyze a report <UploadCloud size={17}/></button></div><div className="hero-art"><div className="orb orb1"/><div className="orb orb2"/><div className="hero-sheet"><div className="sheet-head"><FlaskConical size={20}/><span>LAB SUMMARY</span><span className="sheet-pill">PREVIEW</span></div><div className="fake-line long"/><div className="fake-line medium"/><div className="mini-bars"><i/><i/><i/><i/><i/><i/><i/></div><div className="fake-line short"/><div className="fake-line long"/></div><div className="float-check"><ShieldCheck size={20}/><div><b>Guardrails active</b><small>Review required</small></div></div></div></div>
        <div className="stat-grid"><Stat icon={FileText} label="Saved reports" value={reports.length} note="Local consented history"/><Stat icon={FlaskConical} label="Latest extracted values" value={resultCount} note="Current session"/><Stat icon={ShieldCheck} label="Review flags" value={flaggedCount} note="Check before use"/></div>
        <div className="two-col"><div className="panel"><div className="panel-title"><div><h3>Quick actions</h3><p>Continue where you need to</p></div><Sparkles size={19}/></div><div className="action-list"><QuickAction icon={UploadCloud} title="Analyze a new report" desc="Upload a PDF or image" onClick={() => setTab("analyze")}/><QuickAction icon={GitCompareIcon} title="Compare reports" desc="Review changes between saved reports" onClick={() => setTab("compare")}/><QuickAction icon={MessageCircle} title="Ask about a report" desc="Retrieve extracted values and context" onClick={() => setTab("assistant")}/></div></div>
        <div className="panel"><div className="panel-title"><div><h3>How it works</h3><p>Human review stays in the loop</p></div><ShieldCheck size={19}/></div><div className="steps"><Step n="01" title="Upload" desc="Submit a supported report file."/><Step n="02" title="Extract" desc="MedGemma reads visible report content."/><Step n="03" title="Validate" desc="Structured checks flag uncertainty."/><Step n="04" title="Review" desc="Verify against the original report."/></div></div></div>
        <SafetyBanner/>
      </section>}

      {tab === "analyze" && <section className="page">
        <div className="section-intro"><div><h2>Analyze a lab report</h2><p>Extract report values into a structured, reviewable format.</p></div><span className="soft-badge"><ShieldCheck size={15}/> Guardrails enabled</span></div>
        <div className="panel upload-panel"><div className="dropzone"><div className="upload-icon"><UploadCloud size={27}/></div><h3>Upload your lab report</h3><p>PDF, PNG, JPG or WEBP · Up to 10 MB · PDF page 1 only</p><label className="file-button">Choose file<input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={e => setFile(e.target.files?.[0] || null)}/></label>{file && <div className="selected-file"><FileText size={17}/><span>{file.name}</span><small>{(file.size/1024/1024).toFixed(2)} MB</small><button onClick={() => setFile(null)}><X size={15}/></button></div>}</div>
        <label className="consent-row"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/><span><b>Save this report to local history</b><small>Optional. Saved report values go into the local SQLite database so you can compare or ask follow-up questions.</small></span></label>
        <div className="upload-footer"><span><ShieldCheck size={16}/> Report contents are not logged by the app.</span><button className="primary" onClick={analyze} disabled={busy || !file}>{busy ? <><LoaderCircle className="spin" size={17}/> Analyzing…</> : <>Analyze report <ArrowUpRight size={17}/></>}</button></div></div>
        {analysis && <AnalysisView result={selectedAnalysis} reportId={analysis.report_id}/>}
        <SafetyBanner/>
      </section>}

      {tab === "compare" && <section className="page"><div className="section-intro"><div><h2>Compare saved reports</h2><p>Compare matching biomarker values. Unit mismatches are flagged instead of converted.</p></div></div>
        <div className="panel"><div className="compare-selects"><label>Previous report<select value={previousId} onChange={e => setPreviousId(e.target.value)}><option value="">Select report</option>{reports.map(r=><option key={r.report_id} value={r.report_id}>{r.filename} · {safeDate(r.created_at)}</option>)}</select></label><div className="compare-arrow"><ArrowDownRight size={20}/></div><label>Current report<select value={currentId} onChange={e => setCurrentId(e.target.value)}><option value="">Select report</option>{reports.map(r=><option key={r.report_id} value={r.report_id}>{r.filename} · {safeDate(r.created_at)}</option>)}</select></label><button className="primary" onClick={compare} disabled={!previousId || !currentId || previousId === currentId}>Compare reports</button></div></div>
        {comparison && <div className="panel"><div className="panel-title"><div><h3>Comparison results</h3><p>{comparison.items.length} biomarker rows · arithmetic only</p></div><span className="soft-badge">Not a diagnosis</span></div><div className="table-wrap"><table><thead><tr><th>Biomarker</th><th>Previous</th><th>Current</th><th>Change</th><th>Review status</th></tr></thead><tbody>{comparison.items.map((i,idx)=><tr key={idx}><td><b>{i.biomarker}</b></td><td>{fmt(i.previous_value)} {i.previous_unit||""}</td><td>{fmt(i.current_value)} {i.current_unit||""}</td><td>{fmt(i.change)}{i.change_percent!==null && i.change_percent!==undefined ? ` (${i.change_percent}%)` : ""}</td><td><span className={`status ${i.status==="comparable"?"status-ok":"status-warn"}`}>{i.status.replaceAll("_"," ")}</span><small className="cell-note">{i.note}</small></td></tr>)}</tbody></table></div><p className="disclaimer">{comparison.safety_note}</p></div>}
        {!reports.length && <EmptyState title="No saved reports yet" desc="Analyze a report and choose to save it to enable comparisons." onClick={() => setTab("analyze")}/>}<SafetyBanner/></section>}

      {tab === "assistant" && <section className="page"><div className="section-intro"><div><h2>Report Q&A</h2><p>Ask about extracted values. Responses are grounded in stored report data and curated notes.</p></div><span className="soft-badge"><MessageCircle size={15}/> Grounded lookup</span></div>
        <div className="panel chat-panel"><div className="chat-header"><div className="assistant-avatar"><Sparkles size={20}/></div><div><b>Labwise assistant</b><small>Report-specific information · No diagnosis</small></div><span className="online-label"><span/> Ready</span></div><label className="field">Choose a saved report<select value={chatReport} onChange={e => setChatReport(e.target.value)}><option value="">Select report</option>{reports.map(r=><option key={r.report_id} value={r.report_id}>{r.filename} · {safeDate(r.created_at)}</option>)}</select></label>
        <div className="suggested"><span>TRY ASKING</span>{["What hemoglobin value was extracted?","What does the reference range mean?","How should I verify a missing unit?"].map(q=><button key={q} onClick={() => setQuestion(q)}>{q}</button>)}</div>
        <textarea value={question} onChange={e => setQuestion(e.target.value)} maxLength={1000} placeholder="Ask a question about this saved report…"/><div className="chat-submit"><small>Voice input uses your browser's speech recognition, if supported.</small><button className="secondary" onClick={() => { const SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (!SR) { setError("Voice input is not supported in this browser. Try a recent version of Chrome or Edge."); return; } const rec = new SR(); rec.lang = "en-IN"; rec.interimResults = false; rec.onresult = ev => setQuestion(q => (q ? q + " " : "") + ev.results[0][0].transcript); rec.onerror = () => setError("Voice input failed. Check microphone permission and try again."); rec.start(); }}><Mic size={15}/> Speak question</button></div><div className="chat-submit"><small>{question.length}/1000 · Answers are not medical advice.</small><button className="primary" onClick={ask} disabled={!chatReport || !question.trim()}>Ask question <ArrowUpRight size={16}/></button></div>
        {chatAnswer && <div className="answer-box"><div className="answer-title"><Sparkles size={17}/> Response</div><p>{chatAnswer.answer}</p>{chatAnswer.report_values?.length>0 && <><h4>Matching report values</h4><div className="table-wrap"><table><thead><tr><th>Biomarker</th><th>Value</th><th>Unit</th><th>Range</th><th>Flag</th></tr></thead><tbody>{chatAnswer.report_values.map((r,i)=><tr key={i}><td>{r.biomarker}</td><td>{fmt(r.value)}</td><td>{fmt(r.unit)}</td><td>{fmt(r.reference_range)}</td><td>{fmt(r.lab_flag)}</td></tr>)}</tbody></table></div></>}{chatAnswer.curated_notes?.map((n,i)=><p className="curated-note" key={i}>{n}</p>)}<small>{chatAnswer.guardrail}</small></div>}</div><SafetyBanner/></section>}

      {tab === "history" && <section className="page"><div className="section-intro"><div><h2>Report history</h2><p>Only reports saved with your explicit consent appear here.</p></div><button className="primary" onClick={() => setTab("analyze")}>Upload report <UploadCloud size={16}/></button></div>
        <div className="panel"><div className="panel-title"><div><h3>Saved reports</h3><p>{reports.length} report{reports.length===1?"":"s"} in local history</p></div><button className="icon-btn" onClick={refresh}><RefreshCw size={17}/></button></div>
        {reports.length ? <div className="history-list">{reports.map(r=><div className="history-row" key={r.report_id}><div className="report-file-icon"><FileText size={20}/></div><div className="history-info"><b>{r.filename}</b><small>Saved {new Date(r.created_at).toLocaleString()}</small><small className="muted-id">{r.report_id}</small></div><button className="secondary" onClick={async()=>{try{const d=await api(`/api/reports/${r.report_id}`);setAnalysis(d);setActiveReport(r.report_id);setTab("analyze")}catch(e){setError(e.message)}}}>View report <ArrowUpRight size={15}/></button></div>)}</div> : <EmptyState title="Your history is empty" desc="Choose the local-history consent option when analyzing a report." onClick={() => setTab("analyze")}/>}</div>
        <SafetyBanner/></section>}
      {tab === "advanced" && <section className="page">
        <div className="section-intro"><div><h2>Review, language & evaluation</h2><p>Phase 3 workflows and Phase 4 operational checks. This dashboard does not measure clinical accuracy.</p></div><span className="soft-badge"><ShieldCheck size={15}/> Human review</span></div>
        <div className="panel"><div className="panel-title"><div><h3>Report tools</h3><p>Select a consented report for review, translation, or export.</p></div><ClipboardCheck size={20}/></div>
          <label className="field">Saved report<select value={advancedReport} onChange={async e => { const id=e.target.value; setAdvancedReport(id); setTranslated(null); if(id){try{setReview(await api(`/api/reports/${id}/review`))}catch(err){setError(err.message)}} }}><option value="">Select report</option>{reports.map(r=><option key={r.report_id} value={r.report_id}>{r.filename} · {safeDate(r.created_at)}</option>)}</select></label>
          <div className="two-col"><div className="panel nested-panel"><h3><ClipboardCheck size={17}/> Clinician review workflow</h3><label className="field">Review status<select value={review.status||"pending"} onChange={e=>setReview(v=>({...v,status:e.target.value}))}><option value="pending">Pending review</option><option value="in_review">In review</option><option value="reviewed">Reviewed</option><option value="needs_correction">Needs correction</option></select></label><label className="field">Reviewer identifier (optional)<input value={review.reviewer||""} maxLength={120} onChange={e=>setReview(v=>({...v,reviewer:e.target.value}))} placeholder="Name or role"/></label><label className="field">Review note (optional)<textarea value={review.note||""} maxLength={2000} onChange={e=>setReview(v=>({...v,note:e.target.value}))} placeholder="Record corrections or review notes"/></label><button className="primary" disabled={!advancedReport||reviewBusy} onClick={async()=>{setReviewBusy(true);try{setReview(await api(`/api/reports/${advancedReport}/review`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(review)}));setNotice("Review status saved locally.")}catch(e){setError(e.message)}finally{setReviewBusy(false)}}}>Save review status</button></div>
          <div className="panel nested-panel"><h3><Globe size={17}/> Multilingual summary</h3><p className="helper-text">Translation uses the configured local Ollama model. It may still mistranslate medical terminology.</p><label className="field">Output language<select value={language} onChange={e=>setLanguage(e.target.value)}>{["Hindi","Kannada","Tamil","Telugu","Marathi","Bengali","Spanish","French","English"].map(l=><option key={l}>{l}</option>)}</select></label><button className="primary" disabled={!advancedReport&&!selectedAnalysis} onClick={async()=>{setError("");setTranslated(null);try{let a=selectedAnalysis;if(advancedReport){const saved=await api(`/api/reports/${advancedReport}`);a=saved.analysis}if(!a){throw new Error("Select a saved report first.")}const r=await api("/api/translate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({summary:a.summary,language})});setTranslated(r)}catch(e){setError(e.message)}}}>Translate current analysis</button>{translated&&<div className="answer-box"><b>{translated.language} translation</b><p>{translated.translated_summary}</p><small>{translated.warning}</small></div>}</div></div>
          <div className="export-row"><div><b>FHIR R4 export</b><small>Creates a basic FHIR Bundle from extracted values. Patient identity is omitted.</small></div><button className="secondary" disabled={!advancedReport} onClick={async()=>{try{const d=await api(`/api/reports/${advancedReport}/fhir`);const blob=new Blob([JSON.stringify(d,null,2)],{type:"application/fhir+json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`lab-report-${advancedReport.slice(0,8)}-fhir.json`;a.click();URL.revokeObjectURL(url)}catch(e){setError(e.message)}}}><Download size={15}/> Export FHIR JSON</button></div>
        </div>
        <div className="panel"><div className="panel-title"><div><h3>Evaluation dashboard</h3><p>Operational quality indicators based on saved reports only.</p></div><button className="secondary" onClick={async()=>{try{setEvaluation(await api("/api/evaluation"))}catch(e){setError(e.message)}}}><RefreshCw size={15}/> Refresh metrics</button></div>
          {evaluation ? <><div className="stat-grid"><Stat icon={FileText} label="Saved reports" value={evaluation.saved_reports} note="Consent-based history"/><Stat icon={FlaskConical} label="Extracted rows" value={evaluation.biomarkers_extracted} note="All saved reports"/><Stat icon={ShieldCheck} label="Review required" value={evaluation.reports_requiring_review} note="Safety workflow"/><Stat icon={AlertCircle} label="Missing values" value={evaluation.missing_numeric_values} note="Extraction checks"/></div><p className="disclaimer">{evaluation.scope_note}</p></> : <p className="helper-text">Select Refresh metrics to load operational counts. These counts are not accuracy measurements.</p>}
        </div><SafetyBanner/></section>}
      <footer className="footer">Labwise · Phases 2–4 prototype <span>For development and educational use only</span></footer>
    </main>
  </div>;
}

function Stat({icon:Icon,label,value,note}){return <div className="stat-card"><div className="stat-top"><span>{label}</span><div className="stat-icon"><Icon size={18}/></div></div><div className="stat-value">{value}</div><small>{note}</small></div>}
function QuickAction({icon:Icon,title,desc,onClick}){return <button className="quick-action" onClick={onClick}><span className="quick-icon"><Icon size={19}/></span><span className="quick-copy"><b>{title}</b><small>{desc}</small></span><ArrowUpRight size={17}/></button>}
function Step({n,title,desc}){return <div className="step"><span>{n}</span><div><b>{title}</b><small>{desc}</small></div></div>}
function GitCompareIcon(props){return <Activity {...props}/>}
function SafetyBanner(){return <div className="safety-banner"><ShieldCheck size={20}/><div><b>Safety note</b><p>This tool does not diagnose conditions or recommend treatment. Verify every extracted value, unit, and reference range against the original report and consult a qualified clinician.</p></div></div>}
function EmptyState({title,desc,onClick}){return <div className="empty"><div><History size={25}/></div><h3>{title}</h3><p>{desc}</p><button className="secondary" onClick={onClick}>Get started <ArrowUpRight size={16}/></button></div>}
function AnalysisView({result,reportId}) {
  if(!result) return null;
  return <div className="panel analysis-panel"><div className="panel-title"><div><h3>Extracted report results</h3><p>{result.results?.length||0} values found · verify against original report</p></div><span className="status status-warn">Review required</span></div>
    <div className="analysis-meta"><div><small>Report date</small><b>{fmt(result.report_date)}</b></div><div><small>Laboratory</small><b>{fmt(result.lab_name)}</b></div><div><small>Saved ID</small><b>{reportId||"Not saved"}</b></div></div>
    <p className="summary-text">{result.summary}</p>
    <div className="table-wrap"><table><thead><tr><th>Biomarker</th><th>Value</th><th>Unit</th><th>Reference range</th><th>Lab flag</th><th>Extraction</th></tr></thead><tbody>{(result.results||[]).map((r,i)=><tr key={i}><td><b>{r.biomarker}</b></td><td>{fmt(r.value_text??r.value)}</td><td>{fmt(r.unit)}</td><td>{fmt(r.reference_range_text??(r.reference_low!=null&&r.reference_high!=null?`${r.reference_low}–${r.reference_high}`:null))}</td><td><span className="status">{fmt(r.lab_flag)}</span></td><td><span className={`status ${r.extraction_status==="extracted"?"status-ok":"status-warn"}`}>{fmt(r.extraction_status)}</span></td></tr>)}</tbody></table></div>
    {result.warnings?.length>0 && <div className="review-flags"><h4><AlertCircle size={16}/> Review flags</h4><ul>{result.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></div>}
  </div>;
}

createRoot(document.getElementById("root")).render(<App/>);
