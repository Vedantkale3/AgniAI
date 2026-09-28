import React, { useRef, useState } from 'react'
import {
  Brain,
  CheckCircle2,
  FileDown,
  FileText,
  Loader2,
  Paperclip,
  Send,
  Wrench,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import {
  downloadDeliverable,
  runAgent,
  runAgentWithImage,
} from '../api/client.js'

const getFilename = (value) => {
  if (!value) return ''
  return String(value).split(/[\\/]/).pop()
}

export default function ChatWorkbench() {
  const [goal, setGoal] = useState('')
  const [file, setFile] = useState(null)
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const [downloadError, setDownloadError] = useState('')
  const fileInputRef = useRef(null)

  const submit = async () => {
    if (!goal.trim() && !file) return

    setLoading(true)
    const currentGoal = goal
    const currentFile = file
    setGoal('')
    setFile(null)

    try {
      const response = currentFile
        ? await runAgentWithImage(currentGoal, currentFile)
        : await runAgent(currentGoal)
      setRuns((previous) => [...previous, response.data])
    } catch (error) {
      setRuns((previous) => [
        ...previous,
        {
          goal: currentGoal,
          error:
            error?.response?.data?.detail ||
            error.message ||
            'Agent request failed.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (value) => {
    const filename = getFilename(value)
    if (!filename) return

    try {
      setDownloadError('')
      const response = await downloadDeliverable(filename)
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream',
      })
      const objectUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(objectUrl)
    } catch {
      setDownloadError('Unable to download the file. Please sign in again.')
    }
  }

  const getDeliverables = (run) =>
    run.deliverable_paths || run.deliverablepaths || []

  return (
    <div className="agent-workbench-reference">
      <header className="page-header">
        <div className="page-title">Agentic Workbench</div>
        <div className="page-desc">
          Describe a goal — drafting an approval note, debugging code, reading a scanned report, running a calculation. The agent plans, calls local tools, and iterates until the deliverable is ready.
        </div>
      </header>

      {!runs.length && !loading && (
        <div className="feature-grid">
          <button type="button" className="feature-card" onClick={() => setGoal('Draft an approval note for replacing the corroded PSV on Reactor R-204 based on the last inspection findings.') }>
            <h3>Try: Approval Note</h3>
            <p>“Draft an approval note for replacing the corroded PSV on Reactor R-204 based on the last inspection findings.”</p>
          </button>
          <button type="button" className="feature-card" onClick={() => setGoal('Write and run a Python script that calculates pump NPSH margin for these flow values: [...]') }>
            <h3>Try: Coding Task</h3>
            <p>“Write and run a Python script that calculates pump NPSH margin for these flow values: [...]”</p>
          </button>
          <button type="button" className="feature-card" onClick={() => setGoal('Summarize the key findings from the attached scanned inspection report and flag anything critical.') }>
            <h3>Try: Document Summary</h3>
            <p>“Summarize the key findings from the attached scanned inspection report and flag anything critical.”</p>
          </button>
          <button type="button" className="feature-card" onClick={() => setGoal('Build a 4-slide board deck on Q2 turnaround progress using the SOP knowledge base.') }>
            <h3>Try: Presentation</h3>
            <p>“Build a 4-slide board deck on Q2 turnaround progress using the SOP knowledge base.”</p>
          </button>
        </div>
      )}

      <div className="run-history">
        {runs.map((run, index) => {
          const deliverables = getDeliverables(run)
          return (
            <div className="panel" key={`${index}-${run.goal || 'run'}`}>
              <div className="run-goal">› {run.goal || 'Agent run'}</div>

              {run.error ? (
                <div className="error-text">{run.error}</div>
              ) : (
                <>
                  {Array.isArray(run.routing_log || run.routinglog) &&
                    (run.routing_log || run.routinglog).map((route, routeIndex) => (
                      <div className="step-tool-tag" key={routeIndex}>
                        <Brain size={12} />
                        ROUTED TO {String(route.selected_model || route.selectedmodel || '').toUpperCase()} · {route.task_type || route.tasktype}
                      </div>
                    ))}

                  {Array.isArray(run.steps) && run.steps.map((step, stepIndex) => (
                    <div className="step-card" key={stepIndex}>
                      <div className="step-tool-tag"><Wrench size={11} /> {step.tool}</div>
                      <div className="step-thought">{step.thought}</div>
                      <div className="step-observation">{String(step.observation || '').slice(0, 800)}</div>
                    </div>
                  ))}

                  <ReactMarkdown>{run.final_answer || run.finalanswer || ''}</ReactMarkdown>

                  {deliverables.length > 0 && (
                    <div className="agni-generated-result">
                      <div className="agni-generated-result-title">
                        <CheckCircle2 size={17} />
                        Deliverable ready
                      </div>
                      <div className="agni-generated-result-subtitle">
                        Saved to the local Deliverables archive.
                      </div>
                      <div className="deliverable-links">
                        {deliverables.map((path) => (
                          <button type="button" className="deliverable-item" key={path} onClick={() => handleDownload(path)}>
                            <FileDown size={14} />
                            <span>{getFilename(path)}</span>
                            <strong>Download</strong>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )
        })}

        {loading && (
          <div className="panel loading-panel">
            <Loader2 size={16} className="spin" />
            Agent is planning and executing steps...
          </div>
        )}
      </div>

      {downloadError && <div className="error-banner">{downloadError}</div>}

      <div className="chat-input-bar">
        <button type="button" className="btn-ghost btn" onClick={() => fileInputRef.current?.click()} title="Attach scanned report or image">
          <Paperclip size={16} />
        </button>
        <input ref={fileInputRef} type="file" hidden accept="image/*,.pdf" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        <input className="chat-text-input" placeholder={file ? `${file.name} — describe what to do with it...` : 'Describe the task...'} value={goal} onChange={(event) => setGoal(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit() } }} disabled={loading} />
        <button type="button" className="btn btn-primary" onClick={submit} disabled={loading || (!goal.trim() && !file)} title="Run agent">
          {loading ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
        </button>
      </div>
    </div>
  )
}
