import { countWords } from '../utils';
import './TextPanel.css';

interface TextPanelProps {
  label: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  minWords?: number;
}

const TextPanel = ({ label, placeholder, value, onChange, minWords = 50 }: TextPanelProps) => {
  const wordCount = countWords(value);
  const meetsMinimum = wordCount >= minWords;

  return (
    <div className="panel">
      <div className="panel__header">
        <h2>{label}</h2>
        <span className={`panel__word-count ${meetsMinimum ? 'ok' : 'warn'}`}>
          {wordCount} words
          {!meetsMinimum && ` (min ${minWords})`}
        </span>
      </div>
      <textarea
        className="panel__textarea"
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={16}
      />
    </div>
  );
};

export default TextPanel;
