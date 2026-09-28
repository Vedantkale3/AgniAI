import React, { useState } from 'react'
import { Zap } from 'lucide-react'
import { previewRouting } from '../api/client.js'

export default function RoutingPreview() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const check = async () => {
    if (!text.trim()) return
    setLoading(true)
    try {
      const res = await previewRouting(text)
      setResult(res.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <div className="panel-title"><Zap size={14}/> Router Preview</div>
      <p style={{fontSize: '11px', color: '#8b98a8', marginBottom: '10px'}}>
        Type a sample request to see which local model the auto-router would pick, and why.
      </p>
      <textarea
        rows={3}
        placeholder="e.g. 'Draft an approval note for the PSV inspection'"
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{
          width: '100%', background: '#0a0e14', border: '1px solid #1f2733',
          borderRadius: '8px', padding: '8px', color: '#e8edf2', fontSize: '12px',
          resize: 'none', marginBottom: '8px'
        }}
      />
      <button className="btn btn-primary" style={{width: '100%'}} onClick={check} disabled={loading}>
        {loading ? 'Checking...' : 'Preview Routing'}
      </button>
      {result && (
        <div style={{marginTop: '12px', fontSize: '12px'}}>
          <div style={{color: '#2dd4bf', fontWeight: 700}}>{result.selected_model}</div>
          <div style={{color: '#5a6675', fontSize: '10.5px', marginTop: '4px'}}>
            Detected: {result.detected_task_type}
          </div>
          <div style={{color: '#8b98a8', fontSize: '10.5px', marginTop: '6px', lineHeight: 1.4}}>
            {result.reason}
          </div>
        </div>
      )}
    </div>
  )
}
