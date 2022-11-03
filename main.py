# -*- coding: utf-8 -*-

from pprint import pprint
from PyInquirer import prompt
from imgcat import imgcat
from prompt_toolkit.validation import Validator, ValidationError
from PIL import Image
import regex

image_path = "./test.jpg"

image = Image.open(image_path)
exif = image.getexif()

print("Here's a photo:")
imgcat(open(image_path))

class FilenameTagValidator(Validator):
    def validate(self, document):
        ok = regex.match('^[a-zA-Z0-9 ]*$', document.text)
        if not ok:
            raise ValidationError(
                message='Please enter valid tags',
                cursor_position=len(document.text))  # Move cursor to end


def promptForCustomDate():
    date_questions = [
        {
            'type': 'input',
            'name': 'date',
            'message': 'Date is missing',
            'default': '',
        }
    ]

    date_answers = prompt(date_questions)
    pprint(date_answers)
    return date_answers["date"]

creation_time = exif.get(36867)
if creation_time is None:
    creation_time = promptForCustomDate()

questions = [
    {
        'type': 'input',
        'name': 'tags',
        'message': 'Enter space separated tags this image taken on ' + creation_time,
        'default': '',
        'validate': FilenameTagValidator,
        'filter': lambda val: val.strip().lower().replace(' ', '-')
    }
]

answers = prompt(questions)

def formatFilename():
    return creation_time + "-" + answers['tags']

final_questions = [
    {
        'type': 'confirm',
        'name': 'confirm',
        'message': 'Does this look correct? ' + formatFilename() ,
        'default': '',
    }
]

final_answers = prompt(final_questions)

filename = formatFilename()

print(filename)