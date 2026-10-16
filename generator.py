"""
Playlist Generator Module for Xoilac M3U8.
Constructs standard M3U/M3U8 playlists conforming strictly to the requested specification:
#EXTM3U

#EXTINF:-1 tvg-id="match_id" tvg-name="Team A vs Team B" tvg-logo="TEAM_A_LOGO_URL" group-title="LIVE | COMPETITION",Team A vs Team B
STREAM_URL
"""

import os
from typing import List, Dict
import logging
from config import DEFAULT_STANDBY_STREAM

logger = logging.getLogger(__name__)


class PlaylistGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def build_m3u(self, matches: List[Dict]) -> str:
        """
        Builds M3U playlist string separating LIVE and UPCOMING matches,
        grouped by competition.
        """
        lines = [
            "#EXTM3U x-tvg-url=\"\" url-tvg=\"\" tvg-shift=\"0\"",
            ""
        ]

        live_matches = [m for m in matches if m.get("is_live")]
        upcoming_matches = [m for m in matches if not m.get("is_live")]

        # Sort matches by kickoff timestamp
        live_matches.sort(key=lambda x: x.get("kickoff_ts", 0))
        upcoming_matches.sort(key=lambda x: x.get("kickoff_ts", 0))

        # ----------------------------------------------------
        # 1. LIVE MATCHES SECTION
        # ----------------------------------------------------
        if live_matches:
            lines.append("########################################################")
            lines.append("## [LIVE] PERTANDINGAN SEDANG BERLANGSUNG")
            lines.append("########################################################")
            lines.append("")

            for m in live_matches:
                entries = self._format_match_entries(m, status_prefix="LIVE")
                lines.extend(entries)

        # ----------------------------------------------------
        # 2. UPCOMING MATCHES SECTION
        # ----------------------------------------------------
        if upcoming_matches:
            lines.append("########################################################")
            lines.append("## [JADWAL] PERTANDINGAN MENDATANG")
            lines.append("########################################################")
            lines.append("")

            for m in upcoming_matches:
                entries = self._format_match_entries(m, status_prefix="UPCOMING")
                lines.extend(entries)

        content = "\n".join(lines)
        return content

    def _format_match_entries(self, match: Dict, status_prefix: str) -> List[str]:
        """
        Formats a single match into #EXTINF block and stream URL.
        """
        match_id = match.get("match_id", "")
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        home_logo = match.get("home_logo") or match.get("league_logo") or ""
        competition = match.get("competition", "Sepak Bola")
        kickoff_str = match.get("kickoff_display", "")
        streams = match.get("streams", [])

        # Format group-title: e.g. "LIVE | Premier League" or "UPCOMING | Liga 1 Indonesia"
        group_title = f"{status_prefix} | {competition}"
        match_title = f"{home} vs {away}"

        # Display name with context
        if status_prefix == "LIVE":
            score_str = f" [{match.get('score')}]" if match.get("score") and match.get("score") != "VS" else ""
            display_title = f"{home} vs {away} (LIVE{score_str})"
        else:
            time_tag = f"[{kickoff_str}] " if kickoff_str else ""
            display_title = f"{time_tag}{home} vs {away}"

        # Determine target streams
        urls_to_emit = streams if streams else [DEFAULT_STANDBY_STREAM]

        entries = []
        for idx, url in enumerate(urls_to_emit):
            # If multiple servers, append server label
            server_suffix = f" (Server {idx + 1})" if len(urls_to_emit) > 1 else ""
            item_display = f"{display_title}{server_suffix}"
            item_id = f"{match_id}_srv{idx+1}" if len(urls_to_emit) > 1 else match_id

            # Standard #EXTINF with attributes
            # Attributes: tvg-id, tvg-name, tvg-logo, group-title, tvg-country, tvg-language
            extinf = (
                f'#EXTINF:-1 tvg-id="{item_id}" '
                f'tvg-name="{match_title}" '
                f'tvg-logo="{home_logo}" '
                f'group-title="{group_title}" '
                f'tvg-country="ID" '
                f'tvg-language="Indonesian" '
                f'catchup="false",'
                f'{item_display}'
            )

            entries.append(extinf)
            entries.append(url)
            entries.append("")

        return entries

    def save_to_file(self, content: str) -> str:
        """
        Writes the playlist content to the destination M3U file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Playlist successfully written to {self.output_path}")
        return self.output_path
