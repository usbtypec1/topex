import json

from config import ROOT_PATH


JSON_FILE_PATH = ROOT_PATH / 'const.json'
const_file = json.loads(JSON_FILE_PATH.read_text(encoding="utf-8"))

const_ru: dict = const_file["ru"]


def is_const(word):
    for value in const_ru.values():
        if word == value:
            return True

    return False
