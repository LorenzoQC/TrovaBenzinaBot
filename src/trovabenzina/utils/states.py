"""
ConversationHandler state IDs are defined once here
so they stay unique across all handlers.
"""
STEP_LANG, STEP_FUEL, STEP_SERVICE = range(3)
STEP_FIND_LOC, STEP_FIND_RADIUS = range(3, 5)
STEP_FAV_ACTION, STEP_FAV_NAME, STEP_FAV_LOC = range(5, 8)
STEP_FAV_REMOVE = 8
