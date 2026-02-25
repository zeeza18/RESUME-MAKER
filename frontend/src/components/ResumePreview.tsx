import { useState } from 'react';
import { ATSCheckResult } from '../types';
import './ResumePreview.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8002';

interface ResumePreviewProps {
  original: string;
  tailored: string;
  jobDescription: string;
}

const ResumePreview = ({ original: _original, tailored, jobDescription }: ResumePreviewProps) => {
  const [copied, setCopied] = useState(false);
  const [atsResult, setAtsResult] = useState<ATSCheckResult | null>(null);
  const [atsLoading, setAtsLoading] = useState(false);
  const [atsError, setAtsError] = useState<string | null>(null);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(tailored);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (error) {
      console.error('Failed to copy:', error);
      setCopied(false);
    }
  };

  const runAtsCheck = async () => {
    setAtsLoading(true);
    setAtsError(null);
    setAtsResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ats/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume: tailored, jobDescription })
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(data.detail ?? 'ATS check failed');
      }

      const data: ATSCheckResult = await response.json();
      setAtsResult(data);
    } catch (err) {
      setAtsError(err instanceof Error ? err.message : 'ATS check failed');
    } finally {
      setAtsLoading(false);
    }
  };

  const downloadPdf = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/pdf/download`);
      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Download failed' }));
        throw new Error(data.detail ?? 'PDF download failed');
      }

      // Extract filename from Content-Disposition header (server sends MOHAMMED_AZEEZULLA_COMPANYNAME.pdf)
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'MOHAMMED_AZEEZULLA_RESUME.pdf'; // Default fallback
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename; // Use dynamic filename from server
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF download failed:', err);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'ats-score--high';
    if (score >= 60) return 'ats-score--mid';
    return 'ats-score--low';
  };

  const wordCount = tailored.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="resume-preview">
      <div className="resume-preview__header">
        <div className="resume-preview__title">
          <h3>Tailored Resume</h3>
          <p className="resume-preview__subtitle">{wordCount.toLocaleString()} words</p>
        </div>
        <div className="resume-preview__actions">
          <button
            type="button"
            onClick={runAtsCheck}
            disabled={atsLoading}
            className="resume-preview__ats-btn"
          >
            {atsLoading ? 'Checking...' : 'ATS Check'}
          </button>
          <button
            type="button"
            onClick={downloadPdf}
            className="resume-preview__pdf-btn"
          >
            Download PDF
          </button>
          <button
            type="button"
            onClick={copyToClipboard}
            className={`resume-preview__copy-btn ${copied ? 'copied' : ''}`}
          >
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
        </div>
      </div>

      {atsError && (
        <div className="ats-result__error">
          {atsError}
          <button type="button" onClick={() => setAtsError(null)}>Dismiss</button>
        </div>
      )}

      {atsResult && (
        <div className="ats-result">
          <div className="ats-result__header">
            <h4>ATS Compatibility Report</h4>
            <span className={`ats-result__score ${getScoreColor(atsResult.score)}`}>
              {atsResult.score}/100
            </span>
          </div>

          <div className="ats-result__grid">
            {atsResult.keywords.keywords && atsResult.keywords.keywords.length > 0 && (
              <div className="ats-result__section">
                <h5>Matched Keywords</h5>
                <div className="ats-result__tags">
                  {atsResult.keywords.keywords.map((kw, i) => (
                    <span key={i} className="ats-result__tag ats-result__tag--match">{kw}</span>
                  ))}
                </div>
              </div>
            )}

            {atsResult.keywords.needs && atsResult.keywords.needs.length > 0 && (
              <div className="ats-result__section">
                <h5>Missing Keywords</h5>
                <div className="ats-result__tags">
                  {atsResult.keywords.needs.map((kw, i) => (
                    <span key={i} className="ats-result__tag ats-result__tag--missing">{kw}</span>
                  ))}
                </div>
              </div>
            )}

            {atsResult.evaluation.ats_optimization && (
              <div className="ats-result__section ats-result__section--full">
                <h5>ATS Optimization Notes</h5>
                <p>{atsResult.evaluation.ats_optimization}</p>
              </div>
            )}

            {atsResult.evaluation.recommendations && atsResult.evaluation.recommendations.length > 0 && (
              <div className="ats-result__section ats-result__section--full">
                <h5>Recommendations</h5>
                <ul>
                  {atsResult.evaluation.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="resume-preview__content">
        <pre>{tailored}</pre>
      </div>
    </div>
  );
};

export default ResumePreview;
