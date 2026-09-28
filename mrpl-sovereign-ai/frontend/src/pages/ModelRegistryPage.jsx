import React, { useEffect, useState } from 'react'
import { Boxes, Eye, Gauge } from 'lucide-react'
import { getModelRegistry } from '../api/client.js'

export default function ModelRegistryPage() {
  const [registry, setRegistry] = useState({})

  useEffect(() => {
    getModelRegistry().then((res) => setRegistry(res.data)).catch(() => {})
  }, [])

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Model Registry</div>
          <div className="page-desc">
            Every model here is a hot-swappable entry. Add a new open-weight model by
            registering it once &mdash; the router re-scores automatically, no redesign needed.
          </div>
        </div>
      </div>

      <div className="feature-grid">
        {Object.entries(registry).map(([key, spec]) => (
          <div className="model-card" key={key} style={{padding: '18px'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <div className="model-card-name">{spec.display_name}</div>
              <div className="model-card-params">{spec.params}</div>
            </div>
            <p style={{fontSize: '12px', color: '#8b98a8', marginTop: '8px', lineHeight: 1.5}}>{spec.notes}</p>
            <div style={{display: 'flex', gap: '14px', marginTop: '10px', fontSize: '11px', color: '#5a6675'}}>
              <span><Gauge size={11} style={{marginRight: '4px'}}/>Speed: {spec.relative_speed}/10</span>
              <span>Ctx: {spec.context_window.toLocaleString()}</span>
              {spec.supports_vision && <span><Eye size={11} style={{marginRight: '4px'}}/>Vision</span>}
            </div>
            <div className="model-tag-list">
              {spec.good_at.map((tag) => <span className="model-tag" key={tag}>{tag}</span>)}
            </div>
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="panel-title"><Boxes size={14}/> Why This Matters</div>
        <p style={{fontSize: '13px', color: '#8b98a8', lineHeight: 1.6}}>
          Most single-model chatbot wrappers hardcode one backend. This workbench treats
          the model layer as a plugin registry: a coding task hits the coder-tuned model,
          a multi-step engineering calculation hits the reasoning-tuned model, a scanned
          drawing hits the vision model, and a quick chat gets routed to the fastest model
          that meets the bar &mdash; all without the user choosing anything manually.
        </p>
      </div>
    </>
  )
}
