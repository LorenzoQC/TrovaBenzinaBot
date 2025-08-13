"""Centralized conversation state IDs for all handlers.

Keeping the IDs in a single module guarantees uniqueness across the bot.
"""

__all__ = [
    "STEP_START_LANGUAGE",
    "STEP_START_FUEL",
    "STEP_SEARCH_LOCATION",
    "STEP_PROFILE_MENU",
    "STEP_PROFILE_LANGUAGE",
    "STEP_PROFILE_FUEL",
]

(
    # /start flow
    STEP_START_LANGUAGE,  # 0 – choose language
    STEP_START_FUEL,  # 1 – choose fuel
    # /search flow
    STEP_SEARCH_LOCATION,  # 2 – ask location or address
    # /profile flow
    STEP_PROFILE_MENU,  # 3 – show profile summary
    STEP_PROFILE_LANGUAGE,  # 4 – choose new language
    STEP_PROFILE_FUEL,  # 5 – choose new fuel
) = range(6)
