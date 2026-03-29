import React from 'react';
import './ButtonHackathon.css';

const ButtonHackathon = ({ children, onClick, variant = 'primary' }) => {
  return (
    <button 
      className={`btn-hackathon btn-${variant}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default ButtonHackathon;