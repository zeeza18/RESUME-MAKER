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
      ? `Round ${roundsCompleted} Complete`
      : normalizedStatus;

  const cards = [
    {
      title: 'Final Score',
      value: typeof finalScore === 'number' ? `${finalScore}/100` : 'N/A',
      accent: 'score'
    },
    {
      title: 'JD Words Captured',
      value: jobWordCount,
      accent: 'jd'
    },
    {
      title: 'Resume Words',
      value: resumeWordCount,
      accent: 'resume'
    },
    {
      title: 'Status',
      value: progressLabel,
      accent: 'status'
    }
  ];

  return (
    <div className="summary-cards">
      {cards.map((card) => (
        <div key={card.title} className={`summary-cards__item ${card.accent}`}>
          <span>{card.title}</span>
          <strong>{card.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;




