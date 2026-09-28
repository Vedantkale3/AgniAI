import React, { useState } from 'react'
import { TerminalSquare, Play } from 'lucide-react'
import { runSandbox } from '../api/client.js'

export default function SandboxPage() {
  const [code, setCode] = useState('# Example: engineering calculation\nimport math\n\nflow_rate = 120  # m3/hr\nhead = 45  # m\nefficiency = 0.72\n\npower_kw = (flow_rate/3600 * 1000 * 9.81 * head) / (efficiency * 1000)\nprint(f"Required pump power: {power_kw:.2f} kW")')
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)

  const execute = async () => {
    setRunning(true)
    try {
      const res = await runSandbox(code)
      setResult(res.data)
    } finally {
      setRunning(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Code Sandbox</div>
          <div className="page-desc">
            Model-generated or hand-written Python runs here in a resource-bounded,
            network-isolated subprocess. The agent uses this same tool internally.
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-title"><TerminalSquare size={14}/> Script</div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={14}
          style={{
            width: '100%', background: '#0a0e14', color: '#a3e7dc', fontFamily: 'monospace',
            fontSize: '12.5px', border: '1px solid #1f2733', borderRadius: '8px', padding: '14px',
            resize: 'vertical'
          }}
        />
        <button className="btn btn-primary" style={{marginTop: '12px'}} onClick={execute} disabled={running}>
          <Play size={13} style={{marginRight: '6px'}}/> {running ? 'Running...' : 'Run in Sandbox'}
        </button>
      </div>

      {result && (
        <div className="panel">
          <div className="panel-title">Output</div>
          <div className="step-observation" style={{maxHeight: '300px'}}>
            {result.stdout || '(no stdout)'}
            {result.stderr && `\n\nSTDERR:\n${result.stderr}`}
          </div>
          <p style={{fontSize: '11px', color: '#5a6675', marginTop: '8px'}}>
            Return code: {result.returncode}
          </p>
        </div>
      )}
    </>
  )
}
