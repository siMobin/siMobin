"use client";

import React, { useEffect, useState } from "react";

interface LanguageStat {
  name: string;
  percentage: number;
}

interface Repo {
  name: string;
  languages_url: string;
}

type LanguageData = { [key: string]: number };

interface GitHubLanguageStatsProps {
  limit?: number; // Optional prop to limit the number of languages displayed
}

const GitHubLanguageStats: React.FC<GitHubLanguageStatsProps> = ({
  limit = 10,
}) => {
  // Default to top 5 languages
  const [languageStats, setLanguageStats] = useState<LanguageStat[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLanguageStats = async () => {
      try {
        const githubUsername = process.env.NEXT_PUBLIC_GITHUB_USERNAME;
        if (!githubUsername) {
          throw new Error(
            "GitHub username not configured. Please set NEXT_PUBLIC_GITHUB_USERNAME in your .env file."
          );
        }

        const githubAccessToken = process.env.NEXT_PUBLIC_GITHUB_ACCESS_TOKEN;
        const headers: HeadersInit = githubAccessToken
          ? { Authorization: `token ${githubAccessToken}` }
          : {};

        const response = await fetch(
          `https://api.github.com/users/${githubUsername}/repos?per_page=100`,
          { headers }
        );
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `GitHub API error: ${response.status} - ${errorText}`
          );
        }
        const data: Repo[] = await response.json();

        const languageByteCounts: { [key: string]: number } = {};
        let totalBytes = 0;

        // Fetch language data for each repository
        const languagePromises = data.map(async (repo: Repo) => {
          const langResponse = await fetch(repo.languages_url, { headers });
          if (!langResponse.ok) {
            console.warn(
              `Could not fetch languages for ${repo.name}: ${langResponse.statusText}`
            );
            return {};
          }
          return langResponse.json();
        });

        const allLanguagesData = await Promise.all(languagePromises);

        allLanguagesData.forEach((langData: LanguageData) => {
          for (const lang in langData) {
            languageByteCounts[lang] =
              (languageByteCounts[lang] || 0) + langData[lang];
            totalBytes += langData[lang];
          }
        });

        const stats: LanguageStat[] = Object.entries(languageByteCounts)
          .map(([name, bytes]) => ({
            name,
            percentage: (bytes / totalBytes) * 100,
          }))
          .sort((a, b) => b.percentage - a.percentage); // Sort by percentage descending

        // Apply the limit after sorting
        setLanguageStats(stats.slice(0, limit));
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

    fetchLanguageStats();
  }, [limit]);

  if (loading) {
    return <div>Loading language stats...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <section className="pt-8">
      <div className="container mx-auto px-4">
        <h2 className="text-2xl font-bold text-center mb-8 text-blue-400">
          Top Languages
        </h2>
        <div className="flex  justify-center gap-8 lg:max-w-4xl mx-auto">
          {languageStats.map((lang) => (
            <div
              key={lang.name}
              className="flex flex-col justify-center items-center"
            >
              <div className="relative w-24 h-24">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  {/* Background circle */}
                  <circle
                    className="text-gray-700"
                    strokeWidth="10"
                    stroke="currentColor"
                    fill="transparent"
                    r="40"
                    cx="50"
                    cy="50"
                  />
                  {/* Progress circle */}
                  <circle
                    className="text-blue-500"
                    strokeWidth="10"
                    strokeDasharray={2 * Math.PI * 40}
                    strokeDashoffset={
                      2 * Math.PI * 40 -
                      (lang.percentage / 100) * (2 * Math.PI * 40)
                    }
                    strokeLinecap="round"
                    stroke="url(#gradient)"
                    fill="transparent"
                    r="40"
                    cx="50"
                    cy="50"
                    style={{
                      transition: "stroke-dashoffset 0.5s ease-out",
                      transform: "rotate(-90deg)",
                      transformOrigin: "50% 50%",
                    }}
                  />
                  <defs>
                    <linearGradient
                      id="gradient"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="0%"
                    >
                      <stop offset="0%" stopColor="#3B82F6" /> {/* Blue-500 */}
                      <stop offset="100%" stopColor="#8B5CF6" />{" "}
                      {/* Purple-600 */}
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">
                    {lang.percentage.toFixed(0)}%
                  </span>
                </div>
              </div>
              <span className="text-white text- mt-2">{lang.name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default GitHubLanguageStats;
