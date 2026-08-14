import PropTypes from 'prop-types';

export default function Card({ children, className = '' }) {
  return (
    <div className={`glass-panel border border-outline-variant clip-path-chamfer p-6 relative flex flex-col ${className}`}>
      {children}
    </div>
  );
}

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};
