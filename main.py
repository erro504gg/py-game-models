# main.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from db.models import Guild, Player, Race, Skill


def _load_players_data() -> List[Dict[str, Any]]:
    file_path = Path(__file__).resolve().parent / "players.json"
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _get_or_create_race(player_data: Dict[str, Any]) -> Race:
    race_data = player_data.get("race") or {}
    name = race_data.get("name") or player_data.get("race_name") or ""
    description = race_data.get("description") or player_data.get(
        "race_description",
        "",
    )
    race, _ = Race.objects.get_or_create(
        name=name,
        defaults={"description": description},
    )
    if description and not race.description:
        race.description = description
        race.save(update_fields=["description"])
    return race


def _get_or_create_guild(player_data: Dict[str, Any]) -> Optional[Guild]:
    guild_data = player_data.get("guild")
    if guild_data is None:
        guild_name = player_data.get("guild_name")
        if not guild_name:
            return None
        guild_desc = player_data.get("guild_description")
        guild, _ = Guild.objects.get_or_create(
            name=guild_name,
            defaults={"description": guild_desc},
        )
        if guild_desc and guild.description is None:
            guild.description = guild_desc
            guild.save(update_fields=["description"])
        return guild

    if isinstance(guild_data, str):
        guild, _ = Guild.objects.get_or_create(name=guild_data)
        return guild

    name = guild_data.get("name") or ""
    description = guild_data.get("description")
    guild, _ = Guild.objects.get_or_create(
        name=name,
        defaults={"description": description},
    )
    if description and guild.description is None:
        guild.description = description
        guild.save(update_fields=["description"])
    return guild


def _create_skills_for_race(
    player_data: Dict[str, Any],
    race: Race,
) -> None:
    skills_data = player_data.get("skills") or []
    for skill_data in skills_data:
        if isinstance(skill_data, str):
            Skill.objects.get_or_create(
                name=skill_data,
                defaults={"bonus": "", "race": race},
            )
            continue

        name = skill_data.get("name") or ""
        bonus = skill_data.get("bonus") or ""
        Skill.objects.get_or_create(
            name=name,
            defaults={"bonus": bonus, "race": race},
        )


def main() -> None:
    players_data = _load_players_data()

    for player_data in players_data:
        race = _get_or_create_race(player_data)
        guild = _get_or_create_guild(player_data)
        _create_skills_for_race(player_data, race)

        nickname = player_data.get("nickname") or ""
        email = player_data.get("email") or ""
        bio = player_data.get("bio") or ""

        Player.objects.get_or_create(
            nickname=nickname,
            defaults={
                "email": email,
                "bio": bio,
                "race": race,
                "guild": guild,
            },
        )
