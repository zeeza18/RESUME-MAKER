import { KeywordAnalysis } from '../types';
import './KeywordBoard.css';

interface KeywordBoardProps {
  data: KeywordAnalysis;
}

const KeywordBoard = ({ data }: KeywordBoardProps) => {
  const sections = [
    { title: 'Keywords', items: data.keywords ?? [], key: 'keywords' },
    { title: 'Needs', items: data.needs ?? [], key: 'needs' },
    { title: 'Results', items: data.results ?? [], key: 'results' }
  ];

  return (
    <div className="keyword-board">
      {sections.map((section) => (
        <div key={section.key} className={`keyword-board__section ${section.key}`}>
          <div className="keyword-board__header">
            <h3>{section.title}</h3>
            <span className="keyword-board__count">{section.items.length}</span>
          </div>
          {section.items.length === 0 ? (
            <p className="keyword-board__empty">No {section.title.toLowerCase()} captured yet</p>
          ) : (
            <ul>
              {section.items.map((item, index) => (
                <li key={`${section.key}-${index}`}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
      {data.error && <p className="keyword-board__error">{data.error}</p>}
    </div>
  );
};

export default KeywordBoard;
