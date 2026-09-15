export default function SidePanel({
  me, displayName, samples, reveal, setReveal, useSample, showTools, setShowTools, hint, solution,
}) {
  return (
    <aside className="side">
      <section className="card challenge">
        <h3>Challenge</h3>
        <ol>
          <li>Enumerate: find another customer's email.</li>
          <li>Exfiltrate their <code>secret_data</code> to <code>{me.attacker_email}</code>.</li>
          <li>Capture the FLAG 🚩</li>
        </ol>
      </section>
      <section className="card">
        <h3>Samples</h3>
        {samples.map(t => (
          <button key={t} className="sample benign" onClick={() => useSample({ text: t })}>
            <span className="tag">Benign</span>
            <span className="txt">{t}</span>
          </button>
        ))}
        {reveal === 'none' && (
          <button className="sample locked" onClick={() => setReveal('hint')}>
            <span className="tag">Hint</span>
            <span className="txt">Stuck? Reveal a hint (exploit stays hidden).</span>
          </button>
        )}
        {reveal !== 'none' && (
          <div className="hint-box">
            <b>Hint</b>
            <p>{hint}</p>
            {reveal === 'hint' ? (
              <button className="link-btn" onClick={() => setReveal('solution')}>Still stuck? Show solution</button>
            ) : (
              <>
                <div className="solution-box">
                  <b>Solution</b>
                  <p><code>{solution}</code></p>
                  <button className="link-btn" onClick={() => useSample({ text: solution })}>Use this prompt</button>
                </div>
                <button className="link-btn" onClick={() => setReveal('none')}>Hide hint &amp; solution</button>
              </>
            )}
          </div>
        )}
      </section>
      <section className="card opts">
        <h3>View</h3>
        <label className="toggle">
          <input type="checkbox" checked={showTools} onChange={e => setShowTools(e.target.checked)} />
          Show AI tool calls
        </label>
        <p className="note">Benign history returns <code title={me.email}>{displayName}</code>. Where is the vuln?</p>
      </section>
    </aside>
  )
}
