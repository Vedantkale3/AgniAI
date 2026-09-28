import React, { useEffect, useState } from 'react'
import { Radar, ShieldAlert, ShieldCheck } from 'lucide-react'
import { networkStatus } from '../api/client.js'

export default function NetworkMonitor() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await networkStatus()
        setStatus(res.data)
      } catch (e) {
        setStatus({ sovereignty_status: 'UNKNOWN', total_connections: 0, local_or_lan: 0, external_flagged: 0 })
      }
    }
    poll()
    const interval = setInterval(poll, 4000)
    return () => clearInterval(interval)
  }, [])

  const sealed = status?.sovereignty_status === 'SEALED'

  return (
    <div className="panel">
      <div className="panel-title"><Radar size={14}/> Network Sentinel</div>
      <div className={`net-monitor-status ${sealed ? 'net-sealed' : 'net-breach'}`}>
        {sealed ? <ShieldCheck size={16}/> : <ShieldAlert size={16}/>}
        {status ? status.sovereignty_status : 'CHECKING...'}
      </div>
      <div className="stat-grid">
        <div className="stat-box">
          <div className="stat-value">{status?.local_or_lan ?? '-'}</div>
          <div className="stat-label">LOCAL / LAN</div>
        </div>
        <div className="stat-box">
          <div className="stat-value" style={{color: status?.external_flagged ? '#ef4444' : '#22c55e'}}>
            {status?.external_flagged ?? '-'}
          </div>
          <div className="stat-label">EXTERNAL FLAGGED</div>
        </div>
      </div>
      <p style={{fontSize: '10.5px', color: '#5a6675', marginTop: '10px', lineHeight: 1.5}}>
        Live process-level egress monitor. Any connection outside loopback / RFC1918
        private LAN space is flagged immediately as a sovereignty breach.
      </p>
    </div>
  )
}
