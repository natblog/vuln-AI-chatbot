import { useState } from 'react'

function toolStatus(t) {
  const r = t.result
  if (r && typeof r === 'object' && r.error) return 'err'
  if (t.name === 'send_email' && r && r.flag_captured) return 'flag'
  return 'ok'
}

export default function ToolCalls({ tools, planner }) {
  const [open, setOpen] = useState(true)
  const via = planner === 'ai' ? ' · via AI' : ''
  return (
    <div className="tools-box">
      <button className="tools-head" onClick={() => setOpen(o => !o)}>
        <span>🔧 {tools.length} tool call{tools.length > 1 ? 's' : ''}{via}</span>
        <span>{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className={`tools-list${tools.length > 2 ? ' many' : ''}`}>
          {tools.map((t, i) => (
            <div key={i} className={`tool-card ${toolStatus(t)}`}>
              <div className="tool-top">
                <span className="tool-num">#{i + 1}</span>
                <code className="tool-name">{t.name}</code>
              </div>
              <div className="tool-summary">{t.summary || t.name}</div>
              <details className="tool-full">
                <summary>args + full result</summary>
                <pre>{JSON.stringify({ args: t.args, result: t.result }, null, 2)}</pre>
              </details>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
