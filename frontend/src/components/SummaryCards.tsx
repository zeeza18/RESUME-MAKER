import './SummaryCards.css';

interface SummaryCardsProps {
  finalScore?: number;
  jobWordCount: number;
  resumeWordCount: number;
  status: string;
  roundsCompleted?: number;
}

const SummaryCards = ({ finalScore, jobWordCount, resumeWordCount, status, roundsCompleted }: SummaryCardsProps) => {
  const normalizedStatus = status.replace(/_/g, ' ').trim() || 'Processing';
  const progressLabel =
    typeof roundsCompleted === 'number' && roundsCompleted > 0
      ? `Round ${roundsCompleted} of 3`
      : normalizedStatus;

  const cards = [
    {
      label: 'Final Score',
      value: typeof finalScore === 'number' ? `${finalScore}/100` : 'N/A',
      accent: 'score'
    },
    {
      label: 'JD Words',
      value: jobWordCount.toLocaleString(),
      accent: 'jd'
    },
    {
      label: 'Resume Words',
      value: resumeWordCount.toLocaleString(),
      accent: 'resume'
    },
    {
      label: 'Progress',
      value: progressLabel,
      accent: 'status'
    }
  ];

  return (
    <div className="summary-cards">
      {cards.map((card) => (
        <div key={card.label} className={`summary-cards__item ${card.accent}`}>
          <span className="summary-cards__label">
            <span className="summary-cards__label-icon" />
            {card.label}
          </span>
          <span className="summary-cards__value">{card.value}</span>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;
