"""
ConversationHandler state IDs are defined once here
so they stay unique across all handlers.
"""
(
    STEP_START_LANGUAGE,  # 0  – choose language (/start)
    STEP_START_FUEL,  # 1  – choose fuel

    STEP_FIND_LOCATION,  # 2  – ask location or address (/find)

    STEP_PROFILE_MENU,  # 3  – show profile summary (/profile)
    STEP_PROFILE_LANGUAGE,  # 4  – choose new language
    STEP_PROFILE_FUEL,  # 5  – choose new fuel
) = range(6)
