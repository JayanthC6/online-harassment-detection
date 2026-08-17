import PropTypes from 'prop-types';

export default function Card({ children, className = '' }) {
  return (
    <div className={`card p-5 ${className}`}>
      {children}
    </div>
  );
}

Card.propTypes = {
  children:  PropTypes.node.isRequired,
  className: PropTypes.string,
};
