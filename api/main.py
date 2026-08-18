"""GitHub profile statistics rendered as a portable SVG card."""

from __future__ import annotations

import hashlib
import asyncio
import html
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

app = FastAPI(title="Git Stats", version="0.1.0")

GITHUB_API = "https://api.github.com"
CACHE_TTL_SECONDS = 15 * 60
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Java": "#B07219",
    "C#": "#178600",
    "C++": "#F34B7D",
    "C": "#555555",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Shell": "#89E051",
    "Dart": "#00B4AB",
}


@dataclass
class CachedStats:
    expires_at: float
    value: dict[str, Any]


_cache: dict[str, CachedStats] = {}


def github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def get_github_stats(username: str) -> dict[str, Any]:
    """Fetch profile data and all public repositories from GitHub REST API."""
    cached = _cache.get(username.lower())
    if cached and cached.expires_at > time.monotonic():
        return cached.value

    async with httpx.AsyncClient(timeout=12) as client:
        profile_response = await client.get(f"{GITHUB_API}/users/{username}", headers=github_headers())
        if profile_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Usuário do GitHub não encontrado.")
        if profile_response.status_code == 403:
            raise HTTPException(status_code=429, detail="Limite da API do GitHub atingido. Configure GITHUB_TOKEN.")
        profile_response.raise_for_status()
        profile = profile_response.json()

        repositories: list[dict[str, Any]] = []
        page = 1
        while True:
            repos_response = await client.get(
                f"{GITHUB_API}/users/{username}/repos",
                headers=github_headers(),
                params={"per_page": 100, "page": page, "type": "owner", "sort": "updated"},
            )
            repos_response.raise_for_status()
            batch = repos_response.json()
            repositories.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        semaphore = asyncio.Semaphore(10)

        async def repository_languages(repo: dict[str, Any]) -> dict[str, int]:
            async with semaphore:
                response = await client.get(repo["languages_url"], headers=github_headers())
                response.raise_for_status()
                return response.json()

        language_sets = await asyncio.gather(*(repository_languages(repo) for repo in repositories))

    language_totals: dict[str, int] = {}
    for languages in language_sets:
        for language, bytes_of_code in languages.items():
            language_totals[language] = language_totals.get(language, 0) + bytes_of_code
    total_bytes = sum(language_totals.values())
    languages = [
        {"name": language, "percentage": round(bytes_of_code / total_bytes * 100, 1)}
        for language, bytes_of_code in sorted(language_totals.items(), key=lambda item: item[1], reverse=True)[:5]
    ] if total_bytes else []

    stats = {
        "username": profile["login"],
        "name": profile.get("name") or profile["login"],
        "repositories": profile["public_repos"],
        "followers": profile["followers"],
        "following": profile["following"],
        "stars": sum(repo["stargazers_count"] for repo in repositories),
        "languages": languages,
    }
    _cache[username.lower()] = CachedStats(time.monotonic() + CACHE_TTL_SECONDS, stats)
    return stats


def general_card_svg(stats: dict[str, Any], theme: str) -> str:
    palettes = {
        "dark": {"background": "#0d1117", "border": "#30363d", "text": "#f0f6fc", "muted": "#8b949e", "accent": "#58a6ff"},
        "light": {"background": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a", "accent": "#0969da"},
    }
    colors = palettes[theme]
    name = html.escape(stats["name"])
    username = html.escape(stats["username"])
    rows = [
        ("Repositórios públicos", stats["repositories"]),
        ("Estrelas recebidas", stats["stars"]),
        ("Seguidores", stats["followers"]),
        ("Seguindo", stats["following"]),
    ]
    rendered_rows = "".join(
        f'<text x="28" y="{118 + index * 32}" class="label">{label}</text>'
        f'<text x="372" y="{118 + index * 32}" text-anchor="end" class="value">{value:,}</text>'
        for index, (label, value) in enumerate(rows)
    )

    language_rows = "".join(
        f'<text x="28" y="{287 + index * 27}" class="label">{html.escape(language["name"])}</text>'
        f'<rect x="155" y="{276 + index * 27}" width="180" height="8" rx="4" fill="{colors["border"]}"/>'
        f'<rect x="155" y="{276 + index * 27}" width="{180 * language["percentage"] / 100:.1f}" height="8" rx="4" fill="{language_color(language["name"])}"/>'
        f'<text x="372" y="{287 + index * 27}" text-anchor="end" class="value">{language["percentage"]:.1f}%</text>'
        for index, language in enumerate(stats["languages"])
    ) or f'<text x="28" y="287" class="label">Nenhuma linguagem detectada em repositórios públicos.</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="260" role="img" aria-label="General statistics for {username}">
  <style>
    .title {{ font: 700 20px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["text"]}; }}
    .handle {{ font: 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["muted"]}; }}
    .label {{ font: 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["muted"]}; }}
    .value {{ font: 700 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["text"]}; }}
  </style>
  <rect x="0.5" y="0.5" width="399" height="259" rx="12" fill="{colors["background"]}" stroke="{colors["border"]}"/>
  <rect x="28" y="30" width="5" height="45" rx="2.5" fill="{colors["accent"]}"/>
  <text x="47" y="50" class="title">{name}</text>
  <text x="47" y="70" class="handle">@{username}</text>
  <line x1="28" y1="90" x2="372" y2="90" stroke="{colors["border"]}"/>
  {rendered_rows}
  <text x="28" y="238" class="handle">Atualizado pela API do GitHub</text>
</svg>'''


def languages_card_svg(stats: dict[str, Any], theme: str) -> str:
    palettes = {
        "dark": {"background": "#0d1117", "border": "#30363d", "text": "#f0f6fc", "muted": "#8b949e"},
        "light": {"background": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a"},
    }
    colors = palettes[theme]
    username = html.escape(stats["username"])
    language_rows = "".join(
        f'<text x="28" y="{108 + index * 27}" class="label">{html.escape(language["name"])}</text>'
        f'<rect x="155" y="{97 + index * 27}" width="180" height="8" rx="4" fill="{colors["border"]}"/>'
        f'<rect x="155" y="{97 + index * 27}" width="{180 * language["percentage"] / 100:.1f}" height="8" rx="4" fill="{language_color(language["name"])}"/>'
        f'<text x="372" y="{108 + index * 27}" text-anchor="end" class="value">{language["percentage"]:.1f}%</text>'
        for index, language in enumerate(stats["languages"])
    ) or '<text x="28" y="108" class="label">No language data found.</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="280" role="img" aria-label="Most used languages for {username}">
  <style>
    .title {{ font: 700 20px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["text"]}; }}
    .handle {{ font: 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["muted"]}; }}
    .label {{ font: 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["muted"]}; }}
    .value {{ font: 700 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: {colors["text"]}; }}
  </style>
  <rect x="0.5" y="0.5" width="399" height="279" rx="12" fill="{colors["background"]}" stroke="{colors["border"]}"/>
  <text x="28" y="48" class="title">Linguagens mais usadas</text>
  <text x="28" y="70" class="handle">@{username}</text>
  <line x1="28" y1="82" x2="372" y2="82" stroke="{colors["border"]}"/>
  {language_rows}
  <text x="28" y="258" class="handle">Atualizado pela API do GitHub</text>
</svg>'''


def language_color(language: str) -> str:
    known_color = LANGUAGE_COLORS.get(language)
    if known_color:
        return known_color

    digest = hashlib.sha256(language.encode("utf-8")).hexdigest()
    hue = int(digest[:8], 16) % 360
    return f"hsl({hue}, 65%, 55%)"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/{username}", response_class=Response)
async def stats_card(username: str, theme: str = Query("dark", pattern="^(dark|light)$")) -> Response:
    stats = await get_github_stats(username)
    return Response(
        content=general_card_svg(stats, theme),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=900"},
    )


@app.get("/{username}/languages", response_class=Response)
async def languages_card(username: str, theme: str = Query("dark", pattern="^(dark|light)$")) -> Response:
    stats = await get_github_stats(username)
    return Response(
        content=languages_card_svg(stats, theme),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=900"},
    )
