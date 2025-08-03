"""
ConversationHandler state IDs are defined once here
so they stay unique across all handlers.
"""
(
    STEP_START_LANGUAGE,  # 0  – choose language (/start)
    STEP_START_FUEL,  # 1  – choose fuel
    STEP_START_SERVICE,  # 2  – choose service/self

    STEP_FIND_LOCATION,  # 3  – ask location or address (/find)

    STEP_PROFILE_MENU,  # 4  – show profile summary (/profile)
    STEP_PROFILE_LANGUAGE,  # 5  – choose new language
    STEP_PROFILE_FUEL,  # 6  – choose new fuel
    STEP_PROFILE_SERVICE  # 7  – choose new service/self
) = range(8)
