import React from "react";
import GitHubStats from "./GitHubStats";

const AboutMe: React.FC = () => {
  return (
    <main className="py-16 " id="about">
      <div className="p-4">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-4 text-hero-text-gradient">
          About Me
        </h2>
        <p className=" text-center text-gray-400 mb-12">
          Discover the story behind the code and the passion that drives my work
        </p>

        <div className="flex flex-col lg:flex-row gap-12 items-center">
          <div className="lg:w-1/2 space-y-6 text- text-gray-300">
            <div className="card space-y-4">
              <p>
                Hey there! I&apos;m{" "}
                <span className="text-blue-400 font-semibold">
                  Shakibul Islam
                </span>
                , better known as{" "}
                <span className="text-purple-400 font-semibold">siMobin</span>{" "}
                in the digital world. I&apos;m a passionate Full Stack Developer
                from the vibrant city of Dhaka, Bangladesh.
              </p>
              <p>
                My journey in programming started with curiosity and has evolved
                into a deep passion for creating innovative solutions. I love
                working with modern technologies and frameworks to build
                applications that make a difference.
              </p>
              <p>
                When I&apos;m not coding, you&apos;ll find me exploring new
                technologies, gaming with friends, or contributing to
                open-source projects. I believe in continuous learning and
                sharing knowledge with the community.
              </p>
            </div>

            <div className="card font-mono text-sm">
              <p className="text-green-400">~$ echo $PASSION</p>
              <p>Full Stack Development</p>
              <p className="text-green-400 mt-2">~$ echo $LOCATION</p>
              <p>Dhaka, Bangladesh BD</p>
              <p className="text-green-400 mt-2">~$ echo $STATUS</p>
              <p>Ready to build amazing things ✨</p>
            </div>
          </div>

          <div className="lg:w-1/2 grid grid-cols-1 md:grid-cols-2 gap-8">
            <GitHubStats
              githubUsername={
                process.env.NEXT_PUBLIC_GITHUB_USERNAME || "siMobin"
              }
              githubAccessToken={process.env.NEXT_PUBLIC_GITHUB_ACCESS_TOKEN}
            />
          </div>
        </div>
      </div>
    </main>
  );
};

export default AboutMe;
