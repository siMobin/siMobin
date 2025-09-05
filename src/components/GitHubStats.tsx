"use client";

import React, { useEffect, useState } from "react";

interface GitHubRepo {
  id: number;
  name: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
}

interface GitHubStatsProps {
  githubUsername: string;
  githubAccessToken?: string;
}

const GitHubStats: React.FC<GitHubStatsProps> = ({
  githubUsername,
  githubAccessToken,
}) => {
  const [projectsCount, setProjectsCount] = useState<number>(0);
  const [technologiesCount, setTechnologiesCount] = useState<number>(0);
  const [gitHubStars, setGitHubStars] = useState<number>(0);
  const [totalForks, setTotalForks] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGitHubStats = async () => {
      try {
        if (!githubUsername) {
          throw new Error(
            "GitHub username not provided. Please set NEXT_PUBLIC_GITHUB_USERNAME in your .env file."
          );
        }

        const headers: HeadersInit = githubAccessToken
          ? { Authorization: `token ${githubAccessToken}` }
          : {};

        const response = await fetch(
          `https://api.github.com/users/${githubUsername}/repos?per_page=100`, // Fetch up to 100 repos to get comprehensive stats
          { headers }
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `GitHub API error: ${response.status} - ${errorText}`
          );
        }

        const data: GitHubRepo[] = await response.json();

        // Calculate Projects Count
        setProjectsCount(data.length);

        // Calculate Technologies Count (unique languages)
        const uniqueLanguages = new Set<string>();
        data.forEach((repo) => {
          if (repo.language) {
            uniqueLanguages.add(repo.language);
          }
        });
        setTechnologiesCount(uniqueLanguages.size);

        // Calculate Total GitHub Stars
        const totalStars = data.reduce(
          (sum, repo) => sum + repo.stargazers_count,
          0
        );
        setGitHubStars(totalStars);

        // Calculate Total Forks
        const totalForksCount = data.reduce(
          (sum, repo) => sum + repo.forks_count,
          0
        );
        setTotalForks(totalForksCount);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unknown error occurred.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchGitHubStats();
  }, [githubUsername, githubAccessToken]);

  if (loading) {
    return (
      <>
        <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
          <div className="text-blue-400 text-5xl mb-4">
            <i className="fas fa-code"></i>
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Projects</p>
        </div>
        <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
          <div className="text-blue-400 text-5xl mb-4">
            <i className="fas fa-brain"></i>
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Technologies</p>
        </div>
        <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
          <div className="text-blue-400 text-5xl mb-4">
            <i className="fas fa-heart"></i>
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">GitHub Stars</p>
        </div>
        <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
          <div className="text-blue-400 text-5xl mb-4">
            <i className="fas fa-code-branch"></i>
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Forks</p>
        </div>
      </>
    );
  }

  if (error) {
    return <div className="text-red-500 col-span-full">Error: {error}</div>;
  }

  return (
    <>
      <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
        <div className="text-blue-400 text-5xl mb-4">
          <i className="fas fa-code"></i>
        </div>
        <h3 className="text-4xl font-bold mb-2">{projectsCount}+</h3>
        <p className="text-gray-400">Public Projects</p>
      </div>
      <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
        <div className="text-blue-400 text-5xl mb-4">
          <i className="fas fa-brain"></i>
        </div>
        <h3 className="text-4xl font-bold mb-2">{technologiesCount}+</h3>
        <p className="text-gray-400">Technologies</p>
      </div>
      <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
        <div className="text-blue-400 text-5xl mb-4">
          <i className="fas fa-heart"></i>
        </div>
        <h3 className="text-4xl font-bold mb-2">{gitHubStars}+</h3>
        <p className="text-gray-400">GitHub Stars</p>
      </div>
      <div className="card flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10 ">
        <div className="text-blue-400 text-5xl mb-4">
          <i className="fas fa-code-branch"></i>
        </div>
        <h3 className="text-4xl font-bold mb-2">{totalForks}+</h3>
        <p className="text-gray-400">Forks</p>
      </div>
    </>
  );
};

export default GitHubStats;
