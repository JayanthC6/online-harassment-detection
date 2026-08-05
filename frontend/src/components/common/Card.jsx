import PropTypes from 'prop-types';

export default function Card({ children, className = '' }) {
  return (
    <div className={`glass-card p-6 ${className}`}>
      {children}
    </div>
  );
}

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
};
