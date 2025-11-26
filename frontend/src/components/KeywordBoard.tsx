import { KeywordAnalysis } from '../types';
import './KeywordBoard.css';

interface KeywordBoardProps {
  data: KeywordAnalysis;
}

const KeywordBoard = ({ data }: KeywordBoardProps) => {
  const sections = [
    { title: 'Keywords', items: data.keywords ?? [] },
    { title: 'Needs', items: data.needs ?? [] },
    { title: 'Results', items: data.results ?? [] }
  ];

  return (
    <div className="keyword-board">
      {sections.map((section) => (
        <div key={section.title} className="keyword-board__section">
          <div className="keyword-board__header">
            <h3>{section.title}</h3>
            <span>{section.items.length}</span>
          </div>
          {section.items.length === 0 ? (
            <p className="keyword-board__empty">No data captured</p>
          ) : (
            <ul>
              {section.items.map((item) => (
                <li key={item}>{item}</li>
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
