import { useState } from 'react';

export default function App() {
  const [jobId, setJobId] = useState<string>();
  const [progress, setProgress] = useState<string>();

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('sample', file);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const { job_id } = await res.json();
      setJobId(job_id);
      setProgress("QUEUED");

      // WebSocket connection - connect directly to API port 8000
      // (Vite proxy doesn't handle WebSocket upgrades well)
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${location.host}/api/ws/${job_id}`);

      ws.onmessage = (ev) => {
        const data = JSON.parse(ev.data);
        setProgress(data.state);
        if (data.state === "DONE") {
          // Provide a link instead of auto-opening which might be blocked
          // But for now, let's try auto-open and show link
          if (data.path) {
            window.open(data.path, "_blank");
          }
        }
      };
    } catch (e) {
      console.error(e);
      setProgress("ERROR");
    }
  };

  return (
    <div className="container">
      <h1>Handwriting Font Generator</h1>
      <p>Upload a filled template to generate your font.</p>

      <div className="actions">
        <a href="/api/template" target="_blank" className="btn secondary">Download Template</a>

        <label className="btn primary">
          Upload Scan
          <input type="file" accept="image/*" onChange={handleUpload} hidden />
        </label>
      </div>

      {progress && (
        <div className="status">
          {jobId && <p>Job ID: <small>{jobId}</small></p>}
          <p>Status: <strong>{progress}</strong></p>
          {progress === "DONE" && (
            <p>Downloading font...</p>
          )}
        </div>
      )}
    </div>
  );
}

