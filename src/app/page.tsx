import { ArrowDown, Github, Linkedin, MapPin, Twitter } from "lucide-react";
import Image from "next/image";
import AboutMe from "@/components/AboutMe";
import GitHubProjects from "@/components/GitHubProjects";
import GitHubLanguageStats from "@/components/GitHubLanguageStats";
import Contact from "@/components/Contact";
import Footer from "@/components/Footer";
import Header from "@/components/Header";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground">
      {/* Header */}
      <Header />
      <main className="flex flex-col items-center justify-center flex-grow text-center relative hero">
        {/* <div className="relative my-8" id="home">
          <div className="w-32 h-32 rounded-full border-2 border-accent flex items-center justify-center profile-pic-container">
            <div className="text-white text-4xl">
              <Image
                src="/images/logo.png"
                alt="siMobin"
                width={100}
                height={100}
              />
            </div>
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 rounded-full border border-dashed border-accent animate-spin-slow profile-pic-wrapper"></div>
          </div>
        </div> */}

        <code className="text-keyword text-lg mb-2">$ whoami</code>
        <h1 className="text-6xl font-bold mb-4 text-hero-text-gradient">
          Md. Shakibul Islam
        </h1>

        <div className="bg-accent/5 backdrop-blur-[3px] border border-accent/20 rounded-lg p-6 mb-8 max-w-lg text-left">
          <pre className="">
            <span className="text-keyword">function</span>{" "}
            <span className="text-function">siMobin</span>() {"{"}
            {"\n  "}
            <span className="text-keyword">return</span>{" "}
            <span className="text-string">
              &quot;Full Stack Developer&quot;
            </span>
            ;{"\n"}
            {"}"}
          </pre>
        </div>

        {/* <p className="text- max-w-2xl mb-8">
          A passionate Full Stack Developer from Bangladesh, crafting digital
          experiences with modern technologies and creative problem-solving.
        </p> */}

        <p className="text-accent flex items-center gap-2 mb-12">
          <MapPin size={16} />
          Dhaka, Bangladesh
        </p>

        <div className="absolute bottom-8 cursor-pointer down-arrow">
          <ArrowDown
            className="bg-accent/10 border border-accent/20 p-1 rounded-full animate-bounce"
            size={32}
          />
        </div>
      </main>
      <AboutMe />
      <main>
        <GitHubProjects limit={3} /> {/* Display top 3 GitHub projects */}
        <GitHubLanguageStats limit={8} /> {/* Display top 5 languages */}
      </main>
      <Contact />
      <Footer />
    </div>
  );
}
