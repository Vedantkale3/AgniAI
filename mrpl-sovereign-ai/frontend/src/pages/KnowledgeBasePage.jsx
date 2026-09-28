import { useEffect, useState } from 'react'
import {
  Database,
  FileWarning,
  LoaderCircle,
  Search,
  ShieldCheck,
  Upload,
} from 'lucide-react'

import {
  ingestDocument,
  kbStats,
  searchKnowledge,
} from '../api/client.js'


const DOCUMENT_TYPES = [
  'SOP',
  'MANUAL',
  'CORRESPONDENCE',
  'INSPECTION_REPORT',
  'DRAWING_NOTES',
]


export default function KnowledgeBasePage() {
  const [file, setFile] = useState(null)
  const [docType, setDocType] = useState('SOP')
  const [isScanned, setIsScanned] = useState(false)
  const [status, setStatus] = useState('')
  const [ingesting, setIngesting] = useState(false)

  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')

  const [stats, setStats] = useState(null)


  function refreshStats() {
    kbStats()
        .then((response) => setStats(response.data))
        .catch(() => {})
  }


  useEffect(() => {
    refreshStats()
  }, [])


  async function upload() {
    if (!file) {
      setStatus('Please choose a document first.')
      return
    }

    setIngesting(true)
    setStatus('Ingesting locally…')

    try {
      const response = await ingestDocument(
          file,
          docType,
          isScanned,
      )

      const data = response.data

      setStatus(
          `Ingested ${data.chunks_ingested} chunk${
              data.chunks_ingested === 1 ? '' : 's'
          } from ${data.file}`,
      )

      setFile(null)
      refreshStats()
    } catch (error) {
      const detail =
          error.response?.data?.detail ||
          error.message ||
          'Failed to ingest document.'

      setStatus(`Ingestion failed: ${detail}`)
    } finally {
      setIngesting(false)
    }
  }


  async function search() {
    const cleanedQuery = query.trim()

    if (!cleanedQuery) {
      setSearchError('Enter a question or search term first.')
      return
    }

    setSearching(true)
    setSearchError('')
    setResults([])

    try {
      const response = await searchKnowledge(cleanedQuery, 5)
      const data = Array.isArray(response.data)
          ? response.data
          : []

      setResults(data)

      if (data.length === 0) {
        setSearchError(
            'No local evidence was found for that query.',
        )
      }
    } catch (error) {
      const detail =
          error.response?.data?.detail ||
          error.message ||
          'Failed to search the Knowledge Base.'

      setSearchError(detail)
    } finally {
      setSearching(false)
    }
  }


  function handleQueryKeyDown(event) {
    if (event.key === 'Enter') {
      event.preventDefault()
      search()
    }
  }


  return (
      <section className="knowledge-page">
        <header className="page-header">
          <div>
            <p className="page-kicker">
              LOCAL RETRIEVAL AUGMENTATION
            </p>

            <h1>Local Knowledge Base</h1>

            <p>
              SOPs, manuals, and past correspondence are embedded and
              searched entirely on-device. Nothing here ever leaves
              the box.
            </p>
          </div>

          {stats && (
              <div className="kb-stat-card">
                <Database size={16} />
                <span>Indexed chunks</span>
                <strong>{stats.total_chunks ?? 0}</strong>
              </div>
          )}
        </header>

        <div className="knowledge-grid">
          <section className="kb-panel">
            <div className="kb-panel-heading">
              <Upload size={18} />
              <h2>Ingest Document</h2>
            </div>

            <label className="kb-file-picker">
              <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(event) => {
                    setFile(event.target.files?.[0] || null)
                  }}
                  disabled={ingesting}
              />

              <span>
              {file
                  ? file.name
                  : 'Choose a PDF, DOCX, or TXT document'}
            </span>
            </label>

            <label className="kb-label" htmlFor="doc-type">
              Document type
            </label>

            <select
                id="doc-type"
                value={docType}
                onChange={(event) => setDocType(event.target.value)}
                disabled={ingesting}
            >
              {DOCUMENT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.replace('_', ' ')}
                  </option>
              ))}
            </select>

            <label className="kb-checkbox">
              <input
                  type="checkbox"
                  checked={isScanned}
                  onChange={(event) => {
                    setIsScanned(event.target.checked)
                  }}
                  disabled={ingesting}
              />

              <span>Scanned document — run OCR first</span>
            </label>

            <button
                className="kb-primary-button"
                type="button"
                onClick={upload}
                disabled={ingesting}
            >
              {ingesting ? (
                  <>
                    <LoaderCircle size={16} className="spin" />
                    Ingesting…
                  </>
              ) : (
                  <>
                    <Upload size={16} />
                    Ingest
                  </>
              )}
            </button>

            {status && (
                <p className="kb-message">{status}</p>
            )}
          </section>

          <section className="kb-panel">
            <div className="kb-panel-heading">
              <Search size={18} />
              <h2>Search Knowledge Base</h2>
            </div>

            <div className="kb-search-row">
              <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={handleQueryKeyDown}
                  placeholder="e.g. What is this document about?"
                  disabled={searching}
              />

              <button
                  className="kb-search-button"
                  type="button"
                  onClick={search}
                  disabled={searching}
                  aria-label="Search Knowledge Base"
              >
                {searching ? (
                    <LoaderCircle size={17} className="spin" />
                ) : (
                    <Search size={17} />
                )}
              </button>
            </div>

            {searchError && (
                <p className="kb-message kb-message-error">
                  {searchError}
                </p>
            )}

            <div className="kb-results">
              {results.map((result, index) => (
                  <article
                      className="kb-result-card"
                      key={`${result.source}-${index}`}
                  >
                    <div className="kb-result-meta">
                  <span>
                    {result.doc_type} · {result.source}
                  </span>

                      {result.low_confidence ? (
                          <span className="kb-badge kb-badge-low">
                      <FileWarning size={12} />
                      Low confidence — verify source
                    </span>
                      ) : (
                          <span className="kb-badge kb-badge-good">
                      <ShieldCheck size={12} />
                      Relevant local evidence
                    </span>
                      )}
                    </div>

                    <p>{result.text}</p>
                  </article>
              ))}

              {!searching &&
                  !searchError &&
                  results.length === 0 && (
                      <p className="kb-empty-state">
                        Search your indexed local documents to view
                        retrieved evidence here.
                      </p>
                  )}
            </div>
          </section>
        </div>
      </section>
  )
}