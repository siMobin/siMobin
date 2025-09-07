import React from "react";

// Function to fetch the latest active repository data
async function fetchLatestRepo() {
  const username = process.env.NEXT_PUBLIC_GITHUB_USERNAME;
  const token = process.env.NEXT_PUBLIC_GITHUB_ACCESS_TOKEN;

  if (!username || !token) {
    console.error(
      "GitHub username or token not found in environment variables."
    );
    return null; // Or handle error appropriately
  }

  try {
    const response = await fetch(
      `https://api.github.com/users/${username}/repos?sort=pushed&direction=desc`,
      {
        headers: {
          Authorization: `token ${token}`,
          Accept: "application/vnd.github.v3+json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.statusText}`);
    }

    const repos = await response.json();

    if (repos && repos.length > 0) {
      // Return the first repository (most recently pushed)
      return repos[0];
    }
    return null;
  } catch (error) {
    console.error("Error fetching GitHub repository:", error);
    return null;
  }
}

// Define the structure of the repository data for type safety
interface Repo {
  name: string;
  html_url: string;
  description: string | null;
  homepage: string | null;
  stargazers_count: number;
  owner: {
    avatar_url: string;
    login: string;
  };
  created_at: string;
}

const LatestRepo = async () => {
  const repo: Repo | null = await fetchLatestRepo();

  if (!repo) {
    return (
      <div
        style={{
          border: "1px solid #ccc",
          padding: "16px",
          borderRadius: "8px",
          margin: "16px",
          fontFamily: "sans-serif",
          color: "#888",
        }}
      >
        Could not load latest GitHub repository. Please check environment
        variables and network connection.
      </div>
    );
  }

  return (
    <div
      style={{
        border: "1px solid #ccc",
        padding: "16px",
        borderRadius: "8px",
        margin: "16px",
        fontFamily: "sans-serif",
      }}
    >
      <h2 style={{ marginBottom: "12px", color: "#333" }}>
        Latest Public Repository:
      </h2>
      <div
        style={{ display: "flex", alignItems: "center", marginBottom: "12px" }}
      >
        <img
          src={repo.owner.avatar_url}
          alt={`${repo.owner.login}'s avatar`}
          style={{
            width: "40px",
            height: "40px",
            borderRadius: "50%",
            marginRight: "12px",
          }}
        />
        <h3>
          <a
            href={repo.html_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ textDecoration: "none", color: "#0366d6" }}
          >
            {repo.name}
          </a>
        </h3>
      </div>
      {repo.description && (
        <p style={{ marginBottom: "12px", color: "#555" }}>
          {repo.description}
        </p>
      )}
      {repo.homepage && (
        <p style={{ marginBottom: "12px", color: "#555" }}>
          Homepage:{" "}
          <a
            href={repo.homepage}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#0366d6" }}
          >
            {repo.homepage}
          </a>
        </p>
      )}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          fontSize: "0.9em",
          color: "#666",
        }}
      >
        <span style={{ marginRight: "16px" }}>
          ⭐ {repo.stargazers_count} Stars
        </span>
        <span>
          📅 Created: {new Date(repo.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
};

export default LatestRepo;
