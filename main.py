# main.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from db.models import Guild, Player, Race, Skill

__all__ = ["main", "Race", "Skill", "Player", "Guild"]


def _load_players() -> List[Dict[str, Any]]:
    path = Path(__file__).resolve().parent / "players.json"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("players"), list):
        return data["players"]

    return []


def _parse_race(player: Dict[str, Any]) -> Tuple[str, str, List[Dict[str, str]]]:
    race_raw: Union[str, Dict[str, Any], None] = player.get("race")

    if isinstance(race_raw, str):
        return race_raw, "", []

    if isinstance(race_raw, dict):
        name = str(race_raw.get("name", "") or "")
        desc = str(race_raw.get("description", "") or "")
        skills = race_raw.get("skills") or []
        return name, desc, skills if isinstance(skills, list) else []

    name = str(player.get("race_name", "") or "")
    desc = str(player.get("race_description", "") or "")
    skills = player.get("race_skills") or []
    return name, desc, skills if isinstance(skills, list) else []


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
