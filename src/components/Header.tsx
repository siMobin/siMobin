import { ArrowDown, Github, Linkedin, MapPin, Twitter } from "lucide-react";
import Link from "next/link";
import React from "react";

const Header: React.FC = () => {
  const currentYear = new Date().getFullYear();
  return (
    <header className="w-full  py-2 border-b border-accent/20 fixed top-0 bg-background/20 backdrop-blur-[5px] shadow-md z-50">
      <div className="lg:mx-30 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-hero-text-gradient">
          siMobin
        </Link>

        <nav>
          <ul className="">
            <Link href="/">Home</Link>
            <a href="#about">About</a>
            <a href="#skills">Skills</a>
            <a href="/projects">Projects</a>
            <a href="#contact">Contact</a>
          </ul>
        </nav>
        <div className="flex space-x-4">
          {/* Social icons would go here */}
          <a href="https://github.com/siMobin" target="_blank">
            <Github className="" size={20} />
          </a>

          <a href="#" target="_blank">
            <Linkedin className="" size={20} />
          </a>

          <a href="#" target="_blank">
            <Twitter className="" size={20} />
          </a>
        </div>
      </div>
    </header>
  );
};

export default Header;
