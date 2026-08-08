import React, { useState, useEffect } from 'react';
import { Download, Play, Music, Video, CheckCircle } from 'lucide-react';

interface Task {
  url: string;
  status: string;
  percent: string;
  speed: string;
  filename?: string;
}

function App() {
  const [urls, setUrls] = useState('');
  const [format, setFormat] = useState('mp3');
  const [batchId, setBatchId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Record<string, Task>>({});
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const handleSubmit = async () => {
    const urlList = urls.split('\n').filter(u => u.trim() !== '');
    if (urlList.length === 0) return;

    try {
      const res = await fetch('http://localhost:8000/api/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls: urlList, format })
      });
      const data = await res.json();
      setBatchId(data.batch_id);
      
      // Initialize task state
      const initialTasks: Record<string, Task> = {};
      urlList.forEach(u => {
        initialTasks[u] = { url: u, status: 'pending', percent: '0%', speed: '0B/s' };
      });
      setTasks(initialTasks);
    } catch (err) {
      console.error(err);
      alert('Failed to connect to backend.');
    }
  };

  useEffect(() => {
    if (batchId) {
      const ws = new WebSocket(`ws://localhost:8000/ws/progress/${batchId}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setTasks(prev => ({
          ...prev,
          [data.url]: {
            ...prev[data.url],
            status: data.status,
            percent: data.percent || prev[data.url]?.percent,
            speed: data.speed || prev[data.url]?.speed,
            filename: data.filename || prev[data.url]?.filename,
          }
        }));
      };
      setSocket(ws);
      return () => ws.close();
    }
  }, [batchId]);

  const tasksArray = Object.values(tasks);
  const allFinished = tasksArray.length > 0 && tasksArray.every(t => t.status === 'finished' || t.status === 'error');

  return (
    <div className="app-container">
      <div className="glass-card">
        <h1>Mass Link Converter</h1>
        <p className="subtitle">Download and convert multiple YouTube videos at once.</p>

        {!batchId ? (
          <>
            <textarea 
              placeholder="Paste YouTube links here (one per line)..."
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
            />
            
            <div className="controls">
              <div className="format-toggle">
                <button 
                  className={`format-btn ${format === 'mp3' ? 'active' : ''}`}
                  onClick={() => setFormat('mp3')}
                >
                  <Music size={18} style={{marginRight: '6px', verticalAlign: 'middle'}}/> MP3
                </button>
                <button 
                  className={`format-btn ${format === 'mp4' ? 'active' : ''}`}
                  onClick={() => setFormat('mp4')}
                >
                  <Video size={18} style={{marginRight: '6px', verticalAlign: 'middle'}}/> MP4
                </button>
              </div>

              <button className="download-btn" onClick={handleSubmit}>
                <Download size={20} /> Convert All
              </button>
            </div>
          </>
        ) : (
          <div className="dashboard">
            <h3>Processing Batch: {batchId.split('-')[0]}...</h3>
            <div className="task-list">
              {Object.values(tasks).map((task, idx) => (
                <div key={idx} className="task-item">
                  <div style={{flex: 1, marginRight: '1rem', overflow: 'hidden'}}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem'}}>
                      <Play size={16} color="#ef4444" />
                      <span style={{fontSize: '0.85rem', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden'}}>{task.filename || task.url}</span>
                    </div>
                    {task.status !== 'finished' && task.status !== 'error' && (
                      <div className="progress-bar">
                        <div className="progress-fill" style={{width: task.percent}}></div>
                      </div>
                    )}
                  </div>
                  <div style={{minWidth: '80px', textAlign: 'right', fontSize: '0.85rem'}}>
                    {task.status === 'finished' ? (
                      <span style={{color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px'}}><CheckCircle size={16}/> Done</span>
                    ) : task.status === 'error' ? (
                      <span style={{color: '#ef4444'}}>Failed</span>
                    ) : (
                      <>
                        <div style={{color: 'var(--primary)'}}>{task.percent}</div>
                        <div style={{color: 'var(--text-muted)'}}>{task.speed}</div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {allFinished && (
              <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center' }}>
                <a 
                  href={`http://localhost:8000/api/download/${batchId}`} 
                  className="download-btn"
                  style={{ textDecoration: 'none' }}
                >
                  <Download size={20} /> Download Zip Archive
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
