"use client";

import {
  Brain,
  GitCommitHorizontal,
  GitFork,
  GitPullRequest,
  SquareDashedBottomCode,
  Star,
} from "lucide-react";
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
  const [totalCommits, setTotalCommits] = useState<number>(0);
  const [totalPullRequests, setTotalPullRequests] = useState<number>(0);
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

        // Fetch total commits
        const commitsResponse = await fetch(
          `https://api.github.com/search/commits?q=author:${githubUsername}`,
          { headers }
        );
        if (!commitsResponse.ok) {
          const errorText = await commitsResponse.text();
          // It's possible to get a 403 here if the user has a lot of commits, so we'll just log it and continue
          console.error(
            `GitHub API error fetching commits: ${commitsResponse.status} - ${errorText}`
          );
          setTotalCommits(0); // Set to 0 or some other default
        } else {
          const commitsData = await commitsResponse.json();
          setTotalCommits(commitsData.total_count);
        }

        // Fetch total pull requests
        const prsResponse = await fetch(
          `https://api.github.com/search/issues?q=author:${githubUsername}+type:pr`,
          { headers }
        );
        if (!prsResponse.ok) {
          const errorText = await prsResponse.text();
          throw new Error(
            `GitHub API error fetching PRs: ${prsResponse.status} - ${errorText}`
          );
        }
        const prsData = await prsResponse.json();
        setTotalPullRequests(prsData.total_count);
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
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <SquareDashedBottomCode size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Projects</p>
        </div>
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <Brain size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Technologies</p>
        </div>
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <Star size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">GitHub Stars</p>
        </div>
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <GitFork size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Forks</p>
        </div>
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <GitCommitHorizontal size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Contribution</p>
        </div>
        <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
          <div className="text-blue-400 text-5xl">
            <GitPullRequest size={32} />
          </div>
          <h3 className="text-4xl font-bold mb-2">...</h3>
          <p className="text-gray-400">Pull Requests</p>
        </div>
      </>
    );
  }

  if (error) {
    return <div className="text-red-500 col-span-full">Error: {error}</div>;
  }

  return (
    <>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <SquareDashedBottomCode size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{projectsCount}+</h3>
        <p className="text-gray-400">Public Projects</p>
      </div>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <Brain size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{technologiesCount}+</h3>
        <p className="text-gray-400">Technologies</p>
      </div>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <Star size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{gitHubStars}+</h3>
        <p className="text-gray-400">GitHub Stars</p>
      </div>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <GitFork size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{totalForks}+</h3>
        <p className="text-gray-400">Forks</p>
      </div>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <GitCommitHorizontal size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{totalCommits}+</h3>
        <p className="text-gray-400">Contribution</p>
      </div>
      <div className="card space-y-2 flex flex-col items-center text-center transform transition duration-300 hover:scale-102 hover:!bg-accent/10">
        <div className="text-blue-400 text-5xl">
          <GitPullRequest size={32} />
        </div>
        <h3 className="text-4xl font-bold mb-2">{totalPullRequests}+</h3>
        <p className="text-gray-400">Pull Requests</p>
      </div>
    </>
  );
};

export default GitHubStats;
