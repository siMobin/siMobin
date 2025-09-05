import React from "react";

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="footer-container">
      <div className="footer-left">
        &copy; {currentYear} Made with <span className="heart-icon">❤️</span>{" "}
        and <span className="coffee-icon">☕</span> by{" "}
        <span className="name">siMobin</span>
      </div>
      <div className="footer-right">
        <span className="dollar-sign">$ </span>
        <span className="code-snippet">
          while(true) {"{"} code(); coffee(); sleep(); {"}"};
        </span>
      </div>
    </footer>
  );
};

export default Footer;
