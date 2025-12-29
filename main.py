# main.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from django.db import connection

from db.models import Guild, Player, Race, Skill

__all__ = ["main", "Race", "Skill", "Player", "Guild"]


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
                "race_id" integer NOT NULL
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
                "race_id" integer NOT NULL,
                "guild_id" integer NULL,
                "created_at" datetime NOT NULL
            )
            """
        )


def _load_players() -> List[Dict[str, Any]]:
    path = Path(__file__).resolve().parent / "players.json"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        players = data.get("players")
        if isinstance(players, list):
            return players

    return []


def _parse_race(
    player: Dict[str, Any],
) -> Tuple[str, str, List[Dict[str, str]]]:
    race_raw: Union[str, Dict[str, Any], None] = player.get("race")

    if isinstance(race_raw, str):
        return race_raw, "", []

    if isinstance(race_raw, dict):
        name = str(race_raw.get("name", "") or "")
        desc = str(race_raw.get("description", "") or "")
        skills = race_raw.get("skills") or []
        skills_list = skills if isinstance(skills, list) else []
        return name, desc, skills_list

    name = str(player.get("race_name", "") or "")
    desc = str(player.get("race_description", "") or "")
    skills = player.get("race_skills") or []
    skills_list = skills if isinstance(skills, list) else []
    return name, desc, skills_list


def _get_or_create_guild(player: Dict[str, Any]) -> Optional[Guild]:
    guild_raw: Union[str, Dict[str, Any], None] = player.get("guild")

    if guild_raw is None:
        return None

    if isinstance(guild_raw, str):
        if not guild_raw:
            return None
        guild, _ = Guild.objects.get_or_create(name=guild_raw)
        return guild

    if isinstance(guild_raw, dict):
        name = str(guild_raw.get("name", "") or "")
        if not name:
            return None
        desc = guild_raw.get("description")
        guild, _ = Guild.objects.get_or_create(
            name=name,
            defaults={"description": desc},
        )
        if desc is not None and guild.description is None:
            guild.description = desc
            guild.save(update_fields=["description"])
        return guild

    return None


def _create_skills(race: Race, skills: List[Any]) -> None:
    for item in skills:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "")
        bonus = str(item.get("bonus", "") or "")
        if not name:
            continue
        Skill.objects.get_or_create(
            name=name,
            defaults={"bonus": bonus, "race": race},
        )


def main() -> None:
    _ensure_tables()

    for player in _load_players():
        race_name, race_desc, race_skills = _parse_race(player)
        race, _ = Race.objects.get_or_create(
            name=race_name,
            defaults={"description": race_desc},
        )
        if race_desc and not race.description:
            race.description = race_desc
            race.save(update_fields=["description"])

        _create_skills(race, race_skills)
        guild = _get_or_create_guild(player)

        nickname = str(player.get("nickname", "") or "")
        email = str(player.get("email", "") or "")
        bio = str(player.get("bio", "") or "")

        Player.objects.get_or_create(
            nickname=nickname,
            defaults={
                "email": email,
                "bio": bio,
                "race": race,
                "guild": guild,
            },
        )
