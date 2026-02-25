import { FormEvent, useMemo, useState } from 'react';
import TextPanel from './components/TextPanel';
import SummaryCards from './components/SummaryCards';
import KeywordBoard from './components/KeywordBoard';
import EvaluationTimeline from './components/EvaluationTimeline';
import ResumePreview from './components/ResumePreview';
import Loader from './components/Loader';
import JobTracker from './components/JobTracker';
import { TailorResponse, ApiError, TailorStreamEvent } from './types';
import { countWords } from './utils';
import './App.css';

type AppTab = 'tailor' | 'jobs';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8002';

const createInitialResult = (jobDescription: string, currentResume: string): TailorResponse => ({
  status: 'processing',
  final_resume: currentResume,
  final_score: 0,
  keyword_analysis: {},
  all_evaluations: [],
  job_description: jobDescription,
  original_resume: currentResume
});

const App = () => {
  const [activeTab, setActiveTab] = useState<AppTab>('tailor');
  const [jobDescription, setJobDescription] = useState('');
  const [currentResume, setCurrentResume] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TailorResponse | null>(null);

  const jobWordCount = useMemo(() => countWords(jobDescription), [jobDescription]);
  const resumeWordCount = useMemo(() => countWords(currentResume), [currentResume]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/tailor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobDescription,
          currentResume
        })
      });

      if (!response.ok) {
        const data: ApiError = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(data.message ?? 'Failed to tailor resume');
      }

      if (!response.body) {
        throw new Error('No response body received from server');
      }

      const baseResult = createInitialResult(jobDescription, currentResume);
      setResult(baseResult);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamActive = true;

      const applyStreamEvent = (payload: TailorStreamEvent, seed: TailorResponse): boolean => {
        switch (payload.event) {
          case 'keywords_extracted':
            setResult((previous) => {
              const base = previous ?? seed;
              return {
                ...base,
                status: payload.status ?? base.status,
                keyword_analysis: payload.keyword_analysis ?? {},
                job_description: payload.job_description,
                original_resume: payload.original_resume
              };
            });
            return true;
          case 'round_complete':
            setResult((previous) => {
              const base = previous ?? seed;
              const evaluations = payload.all_evaluations ?? base.all_evaluations;
              const latestScore = evaluations.length
                ? evaluations[evaluations.length - 1]?.score ?? base.final_score
                : base.final_score;
              const parsedScore = typeof latestScore === 'number'
                ? latestScore
                : Number.parseFloat(String(latestScore ?? ''));

              return {
                ...base,
                status: payload.status ?? base.status,
                keyword_analysis: payload.keyword_analysis ?? base.keyword_analysis,
                final_resume: payload.tailored_resume ?? base.final_resume,
                final_score: Number.isFinite(parsedScore) ? Math.round(parsedScore) : base.final_score,
                all_evaluations: evaluations
              };
            });
            return true;
          case 'complete':
            setResult((previous) => {
              const finalResponse = payload.payload;
              const finalEvaluations = finalResponse.all_evaluations?.length
                ? finalResponse.all_evaluations
                : previous?.all_evaluations ?? [];
              const lastEvaluation = finalEvaluations.length ? finalEvaluations[finalEvaluations.length - 1] : undefined;

              let latestScore: number | undefined;
              if (typeof lastEvaluation?.score === 'number') {
                latestScore = lastEvaluation.score;
              } else if (typeof lastEvaluation?.score === 'string') {
                const numericScore = Number.parseFloat(lastEvaluation.score);
                if (!Number.isNaN(numericScore)) {
                  latestScore = numericScore;
                }
              }

              const fallbackScore = typeof finalResponse.final_score === 'number'
                ? finalResponse.final_score
                : Number.parseFloat(String(finalResponse.final_score ?? ''));

              return {
                ...finalResponse,
                final_resume: previous?.final_resume?.length ? previous.final_resume : finalResponse.final_resume,
                final_score: Number.isFinite(latestScore ?? fallbackScore)
                  ? Math.round(latestScore ?? fallbackScore)
                  : finalResponse.final_score,
                all_evaluations: finalEvaluations
              };
            });
            return false;
          case 'error':
            setError(payload.message ?? 'Tailoring process failed.');
            return false;
          default:
            return true;
        }
      };

      while (streamActive) {
        const { value, done } = await reader.read();
        const chunk = value ?? new Uint8Array();
        buffer += decoder.decode(chunk, { stream: !done });

        let newlineIndex = buffer.indexOf('\n');
        while (newlineIndex >= 0) {
          const raw = buffer.slice(0, newlineIndex).replace(/\r$/, '').trim();
          buffer = buffer.slice(newlineIndex + 1);

          if (raw.length > 0) {
            try {
              const eventData = JSON.parse(raw) as TailorStreamEvent;
              streamActive = applyStreamEvent(eventData, baseResult);
              if (!streamActive) {
                await reader.cancel().catch(() => undefined);
                break;
              }
            } catch (streamError) {
              console.error('Failed to parse stream chunk', streamError, raw);
            }
          }

          newlineIndex = buffer.indexOf('\n');
        }
        if (done) {
          const remaining = buffer.trim();
          if (remaining.length > 0) {
            try {
              const finalEvent = JSON.parse(remaining) as TailorStreamEvent;
              applyStreamEvent(finalEvent, baseResult);
            } catch (streamError) {
              console.error('Failed to parse final stream chunk', streamError, remaining);
            }
          }
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setJobDescription('');
    setCurrentResume('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app__hero">
        <div className="app__hero-content">
          <span className="app__eyebrow">Resume Crew</span>
          <h1>AI-Powered Resume Tailoring</h1>
          <p className="app__subtitle">
            Paste your job description and resume. Our AI extracts keywords, tailors your resume through multiple rounds, and delivers a polished final version.
          </p>
        </div>
        <div className="app__cta">
          <button type="button" onClick={resetForm}>
            Start Over
          </button>
        </div>
      </header>

      <nav className="app__tabs">
        <button
          className={`app__tab ${activeTab === 'tailor' ? 'app__tab--active' : ''}`}
          onClick={() => setActiveTab('tailor')}
        >
          Tailor Resume
        </button>
        <button
          className={`app__tab ${activeTab === 'jobs' ? 'app__tab--active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          Job Tracker
        </button>
      </nav>

      <main>
        {activeTab === 'tailor' && (
          <>
            <form className="app__grid" onSubmit={handleSubmit}>
              <TextPanel
                label="Job Description"
                placeholder="Paste the job description here..."
                value={jobDescription}
                onChange={setJobDescription}
              />
              <TextPanel
                label="Your Resume"
                placeholder="Paste your current resume here..."
                value={currentResume}
                onChange={setCurrentResume}
              />

              <div className="app__actions">
                <div className="app__word-counts">
                  <span className="app__word-count">
                    <strong>{jobWordCount}</strong> JD words
                  </span>
                  <span className="app__word-count">
                    <strong>{resumeWordCount}</strong> resume words
                  </span>
                </div>
                <button type="submit" disabled={loading || jobWordCount < 50 || resumeWordCount < 50}>
                  {loading ? 'Processing...' : 'Tailor Resume'}
                </button>
              </div>
            </form>

            {error && <p className="app__error">{error}</p>}

            {loading && <Loader />}

            {result && (
              <section className="app__results">
                <SummaryCards
                  finalScore={result.final_score}
                  jobWordCount={countWords(result.job_description)}
                  resumeWordCount={countWords(result.final_resume)}
                  status={result.status}
                  roundsCompleted={result.all_evaluations?.length ?? 0}
                />

                <div className="app__section">
                  <h2>Keyword Analysis</h2>
                  <KeywordBoard data={result.keyword_analysis} />
                </div>

                <div className="app__section">
                  <h2>Evaluation Rounds</h2>
                  <EvaluationTimeline evaluations={result.all_evaluations} />
                </div>

                <div className="app__section">
                  <ResumePreview original={result.original_resume} tailored={result.final_resume} jobDescription={result.job_description} />
                </div>
              </section>
            )}
          </>
        )}

        {activeTab === 'jobs' && (
          <JobTracker />
        )}
      </main>
    </div>
  );
};

export default App;
