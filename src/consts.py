MAP_LADDERS = {
    1: 20,
    4: 25,
    13: 46,
    33: 49,
    42: 63,
    50: 69,
    62: 81,
    71: 90,
    74: 92,
}

LONGEST_LADDER = max(MAP_LADDERS.items(), key=lambda item: abs(item[1] - item[0]))


MAP_SNAKES = {
    21: 3,
    27: 5,
    43: 18,
    47: 11,
    54: 31,
    66: 45,
    76: 58,
    89: 53,
    94: 67,
    96: 84,
    97: 85,
    99: 41,
}

LONGEST_SNAKE = max(MAP_SNAKES.items(), key=lambda item: abs(item[0] - item[1]))


HIDDEN_ACHIEVEMENT_IMAGE_URL = "https://storage.yandexcloud.net/eventlab/assets/aukus4/utils/achievement_hidden.png"
