# main.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from django.db import connection

from db.models import Guild, Player, Race, Skill


def _ensure_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "db_race" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "name" varchar(255) NOT NULL UNIQUE,
                "description" text NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "db_guild" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "name" varchar(255) NOT NULL UNIQUE,
                "description" text NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "db_skill" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "name" varchar(255) NOT NULL UNIQUE,
                "bonus" varchar(255) NOT NULL,
                "race_id" bigint NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS "db_player" (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "nickname" varchar(255) NOT NULL UNIQUE,
                "email" varchar(255) NOT NULL,
                "bio" varchar(255) NOT NULL,
                "race_id" bigint NOT NULL,
                "guild_id" bigint NULL,
                "created_at" datetime NOT NULL
            )
            """
        )


def _load_players_data() -> List[Dict[str, Any]]:
    file_path = Path(__file__).resolve().parent / "players.json"
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        players = data.get("players")
        return players if isinstance(players, list) else []
    return []


def _race_from_player(player_data: Dict[str, Any]) -> Dict[str, Any]:
    race_raw: Union[str, Dict[str, Any], None] = player_data.get("race")
    if isinstance(race_raw, str):
        return {"name": race_raw, "description": "", "skills": []}
    if isinstance(race_raw, dict):
        return {
            "name": race_raw.get("name", ""),
            "description": race_raw.get("description", "") or "",
            "skills": race_raw.get("skills") or [],
        }
    return {
        "name": player_data.get("race_name", "") or "",
        "description": player_data.get("race_description", "") or "",
        "skills": player_data.get("race_skills") or [],
    }


def _get_or_create_race(player_data: Dict[str, Any]) -> Race:
    race_data = _race_from_player(player_data)
    name = race_data.get("name", "") or ""
    description = race_data.get("description", "") or ""

    race, _ = Race.objects.get_or_create(
        name=name,
        defaults={"description": description},
    )
    if description and not race.description:
        race.description = description
        race.save(update_fields=["description"])
    return race


def _get_or_create_guild(player_data: Dict[str, Any]) -> Optional[Guild]:
    guild_raw = player_data.get("guild")

    if guild_raw is None:
        return None

    if isinstance(guild_raw, str):
        if not guild_raw:
            return None
        guild, _ = Guild.objects.get_or_create(name=guild_raw)
        return guild

    if isinstance(guild_raw, dict):
        name = guild_raw.get("name", "") or ""
        if not name:
            return None
        description = guild_raw.get("description")
        guild, _ = Guild.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )
        if description is not None and guild.description is None:
            guild.description = description
            guild.save(update_fields=["description"])
        return guild

    guild_name = player_data.get("guild_name")
    if not guild_name:
        return None
    guild_desc = player_data.get("guild_description")
    guild, _ = Guild.objects.get_or_create(
        name=guild_name,
        defaults={"description": guild_desc},
    )
    if guild_desc is not None and guild.description is None:
        guild.description = guild_desc
        guild.save(update_fields=["description"])
    return guild


def _skills_from_player(player_data: Dict[str, Any]) -> List[Any]:
    if isinstance(player_data.get("skills"), list):
        return player_data["skills"]
    race_data = _race_from_player(player_data)
    skills = race_data.get("skills")
    return skills if isinstance(skills, list) else []


def _create_skills_for_race(player_data: Dict[str, Any], race: Race) -> None:
    for skill_data in _skills_from_player(player_data):
        if isinstance(skill_data, str):
            name = skill_data
            bonus = ""
        else:
            name = (skill_data or {}).get("name", "") if isinstance(skill_data, dict) else ""
            bonus = (skill_data or {}).get("bonus", "") if isinstance(skill_data, dict) else ""

        if not name:
            continue

        Skill.objects.get_or_create(
            name=name,
            defaults={"bonus": bonus, "race": race},
        )


def main() -> None:
    _ensure_tables()
    players_data = _load_players_data()

    for player_data in players_data:
        race = _get_or_create_race(player_data)
        guild = _get_or_create_guild(player_data)
        _create_skills_for_race(player_data, race)

        nickname = player_data.get("nickname", "") or ""
        email = player_data.get("email", "") or ""
        bio = player_data.get("bio", "") or ""

        Player.objects.get_or_create(
            nickname=nickname,
            defaults={
                "email": email,
                "bio": bio,
                "race": race,
                "guild": guild,
            },
        )
