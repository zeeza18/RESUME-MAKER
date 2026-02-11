import { EvaluationResult } from '../types';
import './EvaluationTimeline.css';

interface EvaluationTimelineProps {
  evaluations: EvaluationResult[];
}

const EvaluationTimeline = ({ evaluations }: EvaluationTimelineProps) => {
  if (!evaluations.length) {
    return <p className="timeline__empty">Evaluation results will appear here after processing begins.</p>;
  }

  return (
    <div className="timeline">
      {evaluations.map((evaluation, index) => (
        <div key={index} className="timeline__card">
          <div className="timeline__header">
            <div className="timeline__meta">
              <p className="timeline__round">Round {index + 1}</p>
              <div className="timeline__score">
                <span className="timeline__score-value">
                  {typeof evaluation.score === 'number' ? evaluation.score : '--'}
                </span>
                <span className="timeline__score-max">/100</span>
              </div>
            </div>
          </div>

          <details className="timeline__details">
            <summary>View Details</summary>
            <div className="timeline__content">
              {evaluation.experience_evaluation && (
                <div className="timeline__section">
                  <h5>Experience Insights</h5>
                  <p>{evaluation.experience_evaluation}</p>
                </div>
              )}

              {evaluation.ats_optimization && (
                <div className="timeline__section">
                  <h5>ATS Review</h5>
                  <p>{evaluation.ats_optimization}</p>
                </div>
              )}

              {evaluation.feedback && (
                <div className="timeline__section">
                  <h5>Improvement Notes</h5>
                  <p>{evaluation.feedback}</p>
                </div>
              )}

              {evaluation.recommendations && evaluation.recommendations.length > 0 && (
                <div className="timeline__section">
                  <h5>Recommendations</h5>
                  <ul>
                    {evaluation.recommendations.map((item, recIndex) => (
                      <li key={recIndex}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </details>
        </div>
      ))}
    </div>
  );
};

export default EvaluationTimeline;
