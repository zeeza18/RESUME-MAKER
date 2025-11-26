import { EvaluationResult } from '../types';
import './EvaluationTimeline.css';

interface EvaluationTimelineProps {
  evaluations: EvaluationResult[];
}

const EvaluationTimeline = ({ evaluations }: EvaluationTimelineProps) => {
  if (!evaluations.length) {
    return <p className="timeline__empty">Evaluations will appear here after you run the process.</p>;
  }

  return (
    <div className="timeline">
      {evaluations.map((evaluation, index) => (
        <div key={index} className="timeline__card">
          <div className="timeline__header">
            <div>
              <p className="timeline__round">Round {index + 1}</p>
              <h4>{typeof evaluation.score === 'number' ? `${evaluation.score}/100` : 'No score'}</h4>
            </div>
          </div>

          <details>
            <summary>Evaluation breakdown</summary>
            <div className="timeline__section">
              <h5>Experience Insights</h5>
              <p>{evaluation.experience_evaluation ?? 'No experience insights provided.'}</p>
            </div>

            <div className="timeline__section">
              <h5>ATS Review</h5>
              <p>{evaluation.ats_optimization ?? 'No ATS review provided.'}</p>
            </div>

            <div className="timeline__section">
              <h5>Improvement Notes</h5>
              <p>{evaluation.feedback ?? 'No improvement notes provided.'}</p>
            </div>

            <div className="timeline__section">
              <h5>Recommendations</h5>
              <ul>
                {(evaluation.recommendations ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {(!evaluation.recommendations || evaluation.recommendations.length === 0) && (
                  <li>No recommendations provided.</li>
                )}
              </ul>
            </div>
          </details>
        </div>
      ))}
    </div>
  );
};

export default EvaluationTimeline;
