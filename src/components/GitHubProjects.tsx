"use client";

import { GitFork, Github, Star } from "lucide-react";
import React, { useEffect, useState } from "react";

interface GitHubRepo {
  id: number;
  name: string;
  description: string;
  html_url: string;
  stargazers_count: number;
  forks_count: number;
  language: string;
  topics: string[];
}

interface GitHubProjectsProps {
  limit?: number; // Optional prop to limit the number of repositories
  tagLimit?: number; // Optional prop to limit the number of tags per repository
}

const GitHubProjects: React.FC<GitHubProjectsProps> = ({
  limit = 3,
  tagLimit = 6,
}) => {
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRepos = async () => {
      try {
        const githubUsername = process.env.NEXT_PUBLIC_GITHUB_USERNAME;
        const githubAccessToken = process.env.NEXT_PUBLIC_GITHUB_ACCESS_TOKEN;

        if (!githubUsername) {
          throw new Error(
            "GitHub username not configured. Please set NEXT_PUBLIC_GITHUB_USERNAME in your .env file."
          );
        }

        const headers: HeadersInit = githubAccessToken
          ? { Authorization: `token ${githubAccessToken}` }
          : {};

        // Fetch all repositories (or a larger set) to allow client-side sorting
        const response = await fetch(
          `https://api.github.com/users/${githubUsername}/repos?per_page=100`,
          { headers }
        ); // Fetch up to 100 repos
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `GitHub API error: ${response.status} - ${errorText}`
          );
        }
        const data: GitHubRepo[] = await response.json();

        // Sort repositories by a combined metric of stars and forks
        data.sort((a, b) => {
          // Prioritize stars, then forks
          if (b.stargazers_count !== a.stargazers_count) {
            return b.stargazers_count - a.stargazers_count;
          }
          return b.forks_count - a.forks_count;
        });

        // Apply the limit after sorting
        setRepos(data.slice(0, limit));
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

    fetchRepos();
  }, [limit]);

  if (loading) {
    return <div>Loading GitHub projects...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <section className="pt-12" id="projects">
      <div className="container mx-auto px-4">
        <h2 className="text-4xl font-bold text-center mb-8 text-blue-400">
          Top Open-Source Projects
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {repos.map((repo) => (
            <div
              key={repo.id}
              className="bg-gray-900/20 border border-accent/10 p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="mb-2 text-white flex items-center gap-2">
                  <span className="text-lg font-semibold">{repo.name}</span>
                  {repo.language && (
                    <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                      {repo.language}
                    </span>
                  )}
                </div>
                <div className="flex items-center text-gray-400 gap-4">
                  <a href={repo.html_url} target="_blank">
                    <Github size={16} />
                  </a>
                  <div className="flex items-center gap-1">
                    <Star size={16} /> {repo.stargazers_count}
                  </div>
                  <div className="flex items-center gap-1">
                    <GitFork size={16} /> {repo.forks_count}
                  </div>
                </div>
              </div>
              <p className="text-gray-400 mb-4">
                {repo.description || "No description provided."}
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                {repo.topics &&
                  repo.topics.slice(0, tagLimit).map((topic) => (
                    <span
                      key={topic}
                      className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded-full"
                    >
                      {topic}
                    </span>
                  ))}
                {repo.topics && repo.topics.length > tagLimit && (
                  <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded-full">
                    ...
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default GitHubProjects;
