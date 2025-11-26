import { useState } from 'react';
import './ResumePreview.css';

interface ResumePreviewProps {
  original: string;
  tailored: string;
}

const ResumePreview = ({ original: _original, tailored }: ResumePreviewProps) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(tailored);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (error) {
      setCopied(false);
    }
  };

  return (
    <div className="resume-preview">
      <div className="resume-preview__header">
        <h3>Final Tailored Resume</h3>
        <button type="button" onClick={copyToClipboard} className={copied ? 'copied' : ''}>
          {copied ? 'Copied!' : 'Copy Tailored Resume'}
        </button>
      </div>
      <div className="resume-preview__content">
        <pre>{tailored}</pre>
      </div>
    </div>
  );
};

export default ResumePreview;
