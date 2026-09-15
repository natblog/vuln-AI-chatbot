import ReactMarkdown from 'react-markdown'
import ToolCalls from './ToolCalls.jsx'

export default function ChatLog({ msgs, showTools, displayInitial, useSample, samples, pending, msgsRef }) {
  return (
    <div className="msgs" ref={msgsRef}>
      {msgs.length === 0 && (
        <div className="hero">
          <h2>Shop assistant, ready.</h2>
          <p>Ask about products or your orders — hints available in the sidebar.</p>
          <div className="hero-cards">
            {samples.map(t => (
              <button key={t} onClick={() => useSample({ text: t })}>
                <b>Benign</b>
                <span>{t}</span>
              </button>
            ))}
            <button onClick={() => useSample({ text: samples[1] })}>
              <b>Try it</b>
              <span>Start benign, then ask for a hint →</span>
            </button>
          </div>
        </div>
      )}
      {msgs.map((m, i) => (
        <div key={i} className={`row ${m.role}`}>
          <span className="avatar sm">{m.role === 'ai' ? '✦' : displayInitial}</span>
          <div className={`bubble ${m.role}`}>
            {m.role === 'ai' ? <ReactMarkdown>{m.text}</ReactMarkdown> : <pre>{m.text}</pre>}
            {m.role === 'ai' && showTools && m.tools?.length > 0 && (
              <ToolCalls tools={m.tools} planner={m.planner} />
            )}
          </div>
        </div>
      ))}
      {pending && (
        <div className="row ai">
          <span className="avatar sm">✦</span>
          <div className="bubble ai pending"><span className="typing"><i /><i /><i /></span></div>
        </div>
      )}
    </div>
  )
}
