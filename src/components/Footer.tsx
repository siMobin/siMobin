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
        {/* <span className="dollar-sign">$ </span> */}
        <code className="">
          <pre className="text-keyword">while(true){"{"}</pre>
          <pre className="text-function">
            &nbsp;&nbsp;&nbsp;code(); eat(); sleep();
          </pre>
          <pre className="text-keyword">{"};"}</pre>
        </code>
      </div>
    </footer>
  );
};

export default Footer;
