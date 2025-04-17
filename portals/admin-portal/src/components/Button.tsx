import React from 'react';

interface ButtonProps {
  text: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

const Button: React.FC<ButtonProps> = ({ text, onClick, type = 'button', className }) => {
  return (
    <button onClick={onClick} type={type} className={`btn btn-primary ${className}`}>
      {text}
    </button>
  );
};

export default Button;