import React, { useEffect, useMemo, useState } from 'react'
import {
  CheckCircle2,
  Download,
  FileArchive,
  FileSpreadsheet,
  FileText,
  FileType2,
  FileStack,
  Presentation,
  RefreshCw,
} from 'lucide-react'
import {
  downloadDeliverable,
  listDeliverables,
} from '../api/client.js'

const getExtension = (filename) =>
  filename.split('.').pop()?.toLowerCase() || ''

const getIcon = (filename) => {
  const extension = getExtension(filename)
  if (extension === 'docx' || extension === 'doc') return FileText
  if (extension === 'pdf') return FileType2
  if (extension === 'pptx' || extension === 'ppt') return Presentation
  if (extension === 'xlsx' || extension === 'xls' || extension === 'csv') {
    return FileSpreadsheet
  }
  if (extension === 'zip') return FileArchive
  return FileStack
}

const getFileType = (filename) => {
  const extension = getExtension(filename)
  const labels = {
    docx: 'Word document',
    pdf: 'PDF document',
    pptx: 'Presentation',
    xlsx: 'Spreadsheet',
    csv: 'CSV data',
    zip: 'Archive',
  }
  return labels[extension] || `${extension.toUpperCase()} file`
}

export default function DeliverablesPage() {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState('')

  const loadFiles = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await listDeliverables()
      setFiles(response.data || [])
    } catch {
      setError('Unable to load generated documents.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  const totalSize = useMemo(
    () => files.reduce((sum, file) => sum + Number(file.size_kb || 0), 0),
    [files],
  )

  const handleDownload = async (filename) => {
    try {
      setDownloading(filename)
      setError('')
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
      setError('Download failed. Please sign in again and retry.')
    } finally {
      setDownloading('')
    }
  }

  return (
    <main className="agni-deliverables-page">
      <header className="agni-deliverables-header">
        <div>
          <div className="agni-eyebrow">
            <FileStack size={15} />
            DELIVERABLES
          </div>
          <h1>Generated documents</h1>
          <p>
            Every document created by Agent Workbench is saved here and remains
            available for authenticated local download.
          </p>
        </div>
        <button
          className="agni-refresh-button"
          type="button"
          onClick={loadFiles}
          disabled={loading}
        >
          <RefreshCw size={15} className={loading ? 'agni-spin' : ''} />
          Refresh
        </button>
      </header>

      <div className="agni-deliverables-stats">
        <div className="agni-stat-card">
          <span className="agni-stat-value">{files.length}</span>
          <span className="agni-stat-label">FILES AVAILABLE</span>
        </div>
        <div className="agni-stat-card">
          <span className="agni-stat-value">{totalSize.toFixed(1)} KB</span>
          <span className="agni-stat-label">LOCAL STORAGE</span>
        </div>
        <div className="agni-stat-card agni-stat-secure">
          <CheckCircle2 size={18} />
          <span className="agni-stat-value">LOCAL ONLY</span>
          <span className="agni-stat-label">SOVEREIGN OUTPUT</span>
        </div>
      </div>

      {error && <div className="agni-error-banner">{error}</div>}

      <section className="agni-files-panel">
        <div className="agni-files-heading">
          <div>
            <h2>Document archive</h2>
            <p>Generated locally by AGNI AI</p>
          </div>
          <span>{files.length} items</span>
        </div>

        {loading ? (
          <div className="agni-empty-state">Loading local documents…</div>
        ) : files.length === 0 ? (
          <div className="agni-empty-state">
            No deliverables yet. Run a task from Agent Workbench.
          </div>
        ) : (
          <div className="agni-file-list">
            {files.map((file) => {
              const Icon = getIcon(file.name)
              return (
                <article className="agni-file-row" key={file.name}>
                  <div className="agni-file-icon">
                    <Icon size={21} />
                  </div>
                  <div className="agni-file-details">
                    <div className="agni-file-name">{file.name}</div>
                    <div className="agni-file-meta">
                      {getFileType(file.name)}
                      <span>·</span>
                      {file.size_kb} KB
                      <span>·</span>
                      <span className="agni-local-badge">LOCAL</span>
                    </div>
                  </div>
                  <button
                    className="agni-download-button"
                    type="button"
                    onClick={() => handleDownload(file.name)}
                    disabled={downloading === file.name}
                  >
                    <Download size={15} />
                    {downloading === file.name ? 'Downloading…' : 'Download'}
                  </button>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </main>
  )
}
