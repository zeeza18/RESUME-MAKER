import './Loader.css';

const Loader = () => (
  <div className="loader">
    <div className="loader__spinner">
      <div className="loader__ring" />
      <div className="loader__ring-inner" />
    </div>
    <div className="loader__text">
      <p className="loader__title">Tailoring your resume</p>
      <p className="loader__subtitle">This may take a moment...</p>
    </div>
    <div className="loader__progress">
      <span className="loader__dot" />
      <span className="loader__dot" />
      <span className="loader__dot" />
    </div>
  </div>
);

export default Loader;
