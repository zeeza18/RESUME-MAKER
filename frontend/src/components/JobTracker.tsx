import { useState, useEffect, useCallback, useRef } from 'react';
import { Job, ApplyPhase, ApplyStreamEvent } from '../types';
import './JobTracker.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8002';

const PHASES: { key: ApplyPhase; label: string }[] = [
  { key: 'jd_extraction', label: 'Extract JD' },
  { key: 'tailoring', label: 'Tailor Resume' },
  { key: 'pdf_compilation', label: 'Compile PDF' },
  { key: 'form_filling', label: 'Fill & Submit' },
];

interface ApplyProgress {
  jobId: string;
  messages: string[];
  status: 'running' | 'success' | 'failed';
  currentPhase: ApplyPhase | null;
  completedPhases: ApplyPhase[];
  jobDescription: string;
  tailoringScore: number;
  tailoringRound: number;
  pdfReady: boolean;
}

interface JobTrackerProps {
  onApply?: (job: Job) => void;
}

const JobTracker = ({ onApply: _onApply }: JobTrackerProps) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newUrl, setNewUrl] = useState('');
  const [newCompany, setNewCompany] = useState('');
  const [adding, setAdding] = useState(false);
  const [applyProgress, setApplyProgress] = useState<ApplyProgress | null>(null);
  const progressEndRef = useRef<HTMLDivElement>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs`);
      if (!response.ok) throw new Error('Failed to fetch jobs');
      const data = await response.json();
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  /** Stream NDJSON from a response and dispatch ApplyStreamEvents */
  const streamApplyEvents = async (response: Response, jobId: string) => {
    if (!response.body) throw new Error('No response stream');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIdx = buffer.indexOf('\n');
      while (newlineIdx >= 0) {
        const line = buffer.slice(0, newlineIdx).trim();
        buffer = buffer.slice(newlineIdx + 1);

        if (line) {
          try {
            const event: ApplyStreamEvent = JSON.parse(line);
            handleApplyEvent(event, jobId);
          } catch {
            // skip unparseable lines
          }
        }
        newlineIdx = buffer.indexOf('\n');
      }
    }
  };

  const handleApplyEvent = (event: ApplyStreamEvent, _jobId: string) => {
    switch (event.event) {
      case 'started':
        setApplyProgress(prev => prev ? {
          ...prev,
          messages: [...prev.messages, `Started: ${event.url}`],
        } : null);
        break;

      case 'phase':
        setApplyProgress(prev => {
          if (!prev) return null;
          const completed = prev.currentPhase && prev.currentPhase !== event.phase
            ? [...prev.completedPhases.filter(p => p !== prev.currentPhase), prev.currentPhase]
            : prev.completedPhases;
          return {
            ...prev,
            currentPhase: event.phase,
            completedPhases: completed,
            messages: [...prev.messages, event.message],
          };
        });
        break;

      case 'progress':
        setApplyProgress(prev => prev ? {
          ...prev,
          messages: [...prev.messages, event.message],
        } : null);
        break;

      case 'jd_extracted':
        setApplyProgress(prev => prev ? {
          ...prev,
          jobDescription: event.job_description,
          messages: [...prev.messages, event.message],
        } : null);
        break;

      case 'tailoring_round_complete':
        setApplyProgress(prev => prev ? {
          ...prev,
          tailoringRound: event.round,
          tailoringScore: event.score,
          messages: [...prev.messages, event.message],
        } : null);
        break;

      case 'tailoring_complete':
        setApplyProgress(prev => prev ? {
          ...prev,
          tailoringScore: event.score,
          messages: [...prev.messages, event.message],
        } : null);
        break;

      case 'pdf_compiled':
        setApplyProgress(prev => prev ? {
          ...prev,
          pdfReady: true,
          messages: [...prev.messages, event.message],
        } : null);
        break;

      case 'complete':
        setApplyProgress(prev => prev ? {
          ...prev,
          status: event.success ? 'success' : 'failed',
          completedPhases: event.success ? [...PHASES.map(p => p.key)] : prev.completedPhases,
          currentPhase: null,
          messages: [...prev.messages, event.message ?? (event.success ? 'Done!' : `Failed: ${(event.errors ?? []).join(', ')}`)],
        } : null);
        fetchJobs();
        break;

      case 'error':
        setApplyProgress(prev => prev ? {
          ...prev,
          status: 'failed',
          currentPhase: null,
          messages: [...prev.messages, `Error: ${event.message}`],
        } : null);
        fetchJobs();
        break;
    }
  };

  /** One-click: add job + auto-apply */
  const handleAddJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl.trim()) return;

    setAdding(true);
    const tempId = crypto.randomUUID();

    // Immediately show progress panel
    setApplyProgress({
      jobId: tempId,
      messages: ['Saving job and starting auto-apply pipeline...'],
      status: 'running',
      currentPhase: null,
      completedPhases: [],
      jobDescription: '',
      tailoringScore: 0,
      tailoringRound: 0,
      pdfReady: false,
    });

    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs/add-and-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newUrl, company: newCompany }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Failed to start' }));
        throw new Error(data.detail ?? 'Failed to add and apply');
      }

      // Refresh job list to get the newly added job
      fetchJobs();
      setNewUrl('');
      setNewCompany('');

      await streamApplyEvents(response, tempId);
    } catch (err) {
      setApplyProgress(prev => prev ? {
        ...prev,
        status: 'failed',
        messages: [...prev.messages, `Error: ${err instanceof Error ? err.message : 'Unknown error'}`],
      } : null);
    } finally {
      setAdding(false);
    }
  };

  /** Manual apply for an existing job */
  const handleApply = async (job: Job) => {
    setApplyProgress({
      jobId: job.id,
      messages: ['Starting application...'],
      status: 'running',
      currentPhase: null,
      completedPhases: [],
      jobDescription: '',
      tailoringScore: 0,
      tailoringRound: 0,
      pdfReady: false,
    });

    try {
      const response = await fetch(`${API_BASE_URL}/api/apply/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Apply failed' }));
        throw new Error(data.detail ?? 'Failed to start application');
      }

      await streamApplyEvents(response, job.id);
    } catch (err) {
      setApplyProgress(prev => prev ? {
        ...prev,
        status: 'failed',
        messages: [...prev.messages, `Error: ${err instanceof Error ? err.message : 'Unknown error'}`],
      } : null);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete job');
      setJobs(prev => prev.filter(j => j.id !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete job');
    }
  };

  const handleToggleApplied = async (job: Job) => {
    const newStatus = job.status === 'applied' ? 'pending' : 'applied';
    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs/${job.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) throw new Error('Failed to update job');

      const updated = await response.json();
      setJobs(prev => prev.map(j => j.id === job.id ? updated : j));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update job');
    }
  };

  useEffect(() => {
    progressEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [applyProgress?.messages.length]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getStatusBadge = (status: Job['status']) => {
    const badges = {
      pending: { label: 'Pending', class: 'status--pending' },
      applied: { label: 'Applied', class: 'status--applied' },
      failed: { label: 'Failed', class: 'status--failed' },
      in_progress: { label: 'In Progress', class: 'status--progress' },
    };
    const badge = badges[status] || badges.pending;
    return <span className={`job-tracker__status ${badge.class}`}>{badge.label}</span>;
  };

  if (loading) {
    return <div className="job-tracker__loading">Loading jobs...</div>;
  }

  return (
    <div className="job-tracker">
      <div className="job-tracker__header">
        <h2>Job Applications Tracker</h2>
        <span className="job-tracker__count">{jobs.length} jobs</span>
      </div>

      {error && (
        <div className="job-tracker__error">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <form className="job-tracker__add-form" onSubmit={handleAddJob}>
        <input
          type="url"
          placeholder="Job URL (e.g., https://careers.google.com/...)"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          required
          className="job-tracker__input job-tracker__input--url"
        />
        <input
          type="text"
          placeholder="Company (optional)"
          value={newCompany}
          onChange={(e) => setNewCompany(e.target.value)}
          className="job-tracker__input job-tracker__input--company"
        />
        <button type="submit" disabled={adding || !newUrl.trim()} className="job-tracker__add-btn">
          {adding ? 'Applying...' : 'Add Job'}
        </button>
      </form>

      {jobs.length === 0 ? (
        <div className="job-tracker__empty">
          <p>No jobs added yet. Add a job URL above to get started.</p>
        </div>
      ) : (
        <div className="job-tracker__table-wrapper">
          <table className="job-tracker__table">
            <thead>
              <tr>
                <th>Company</th>
                <th>URL</th>
                <th>Date Added</th>
                <th>Date Applied</th>
                <th>Status</th>
                <th>Applied</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className={`job-tracker__row job-tracker__row--${job.status}`}>
                  <td className="job-tracker__company">
                    <strong>{job.company || 'Unknown'}</strong>
                  </td>
                  <td className="job-tracker__url">
                    <a href={job.url} target="_blank" rel="noopener noreferrer" title={job.url}>
                      {job.url.length > 40 ? job.url.substring(0, 40) + '...' : job.url}
                    </a>
                  </td>
                  <td className="job-tracker__date">{formatDate(job.date_added)}</td>
                  <td className="job-tracker__date">{formatDate(job.date_applied)}</td>
                  <td>{getStatusBadge(job.status)}</td>
                  <td className="job-tracker__checkbox">
                    <label className="job-tracker__check-label">
                      <input
                        type="checkbox"
                        checked={job.status === 'applied'}
                        onChange={() => handleToggleApplied(job)}
                        className="job-tracker__check-input"
                      />
                      <span className="job-tracker__checkmark"></span>
                    </label>
                  </td>
                  <td className="job-tracker__actions">
                    {job.status === 'pending' && (
                      <button
                        className="job-tracker__action-btn job-tracker__action-btn--apply"
                        onClick={() => handleApply(job)}
                        disabled={applyProgress?.status === 'running'}
                        title="Auto Apply"
                      >
                        Apply
                      </button>
                    )}
                    <button
                      className="job-tracker__action-btn job-tracker__action-btn--delete"
                      onClick={() => handleDeleteJob(job.id)}
                      title="Delete"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {applyProgress && (
        <div className={`job-tracker__progress job-tracker__progress--${applyProgress.status}`}>
          <div className="job-tracker__progress-header">
            <h4>
              {applyProgress.status === 'running' && 'Auto-Applying...'}
              {applyProgress.status === 'success' && 'Application Submitted'}
              {applyProgress.status === 'failed' && 'Application Failed'}
            </h4>
            {applyProgress.tailoringScore > 0 && (
              <span className="job-tracker__score-badge">
                Score: {applyProgress.tailoringScore}/100
              </span>
            )}
            {applyProgress.status !== 'running' && (
              <button
                className="job-tracker__progress-close"
                onClick={() => setApplyProgress(null)}
              >
                Close
              </button>
            )}
          </div>

          {/* Phase Stepper */}
          <div className="job-tracker__phase-stepper">
            {PHASES.map((phase) => {
              const isDone = applyProgress.completedPhases.includes(phase.key);
              const isActive = applyProgress.currentPhase === phase.key;
              let cls = 'job-tracker__phase-pill';
              if (isDone) cls += ' job-tracker__phase-pill--done';
              else if (isActive) cls += ' job-tracker__phase-pill--active';
              return (
                <div key={phase.key} className={cls}>
                  <span className="job-tracker__phase-dot" />
                  <span className="job-tracker__phase-label">{phase.label}</span>
                  {isActive && applyProgress.tailoringRound > 0 && phase.key === 'tailoring' && (
                    <span className="job-tracker__phase-round">R{applyProgress.tailoringRound}/3</span>
                  )}
                </div>
              );
            })}
          </div>

          <div className="job-tracker__progress-log">
            {applyProgress.messages.map((msg, i) => (
              <div key={i} className="job-tracker__progress-msg">{msg}</div>
            ))}
            <div ref={progressEndRef} />
          </div>
        </div>
      )}

      <div className="job-tracker__summary">
        <div className="job-tracker__stat">
          <span className="job-tracker__stat-value">{jobs.filter(j => j.status === 'applied').length}</span>
          <span className="job-tracker__stat-label">Applied</span>
        </div>
        <div className="job-tracker__stat">
          <span className="job-tracker__stat-value">{jobs.filter(j => j.status === 'pending').length}</span>
          <span className="job-tracker__stat-label">Pending</span>
        </div>
        <div className="job-tracker__stat">
          <span className="job-tracker__stat-value">{jobs.filter(j => j.status === 'failed').length}</span>
          <span className="job-tracker__stat-label">Failed</span>
        </div>
      </div>
    </div>
  );
};

export default JobTracker;
