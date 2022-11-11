# -*- coding: utf-8 -*-

import pprint
from PyInquirer import prompt
from imgcat import imgcat 
from prompt_toolkit.validation import Validator, ValidationError
from PIL import Image
import datetime
import regex
import typer


app = typer.Typer()

class TagValidator(Validator):
    def validate(self, document):
        ok = regex.match('^[a-zA-Z0-9 ]*$', document.text)
        if not ok:
            raise ValidationError(
                message='Please enter valid tags',
                cursor_position=len(document.text))  # Move cursor to end
class DateValidator(Validator): 
    def validate(self, document):
        ok = regex.match('^[0-9\-]*$', document.text)
        if not ok:
            raise ValidationError(
                message='Please enter a valid date',
                cursor_position=len(document.text))  # Move cursor to end

def promptForCustomDate():
    date_questions = [
        {
            'type': 'input',
            'name': 'date',
            'message': 'Please provide a date in ISO-8601:',
            'default': '',
            'validate': DateValidator,
        }
    ]

    date_answers = prompt(date_questions)
    return date_answers["date"]

def promptForTags():
    questions = [
        {
            'type': 'input',
            'name': 'tags',
            'message': 'Please enter a space separated list of tags:',
            'default': '',
            'validate': TagValidator,
            'filter': lambda val: val.strip().lower().replace(' ', '-')
        }
    ]

    answers = prompt(questions)
    return answers["tags"]


def formatFilename(creation_time, tags):
    return creation_time + "-" + tags

def finalConfirmation(filename):
    final_questions = [
        {
            'type': 'confirm',
            'name': 'confirm',
            'message': f'Does this look correct? {filename}',
        },
        {
            'type': 'input',
            'name': 'modify',
            'message': 'Please provide a fixed filename:',
            'default': filename,
            'when': lambda answers: not answers['confirm'],
        }
    ]

    final_answers = prompt(final_questions)

    return final_answers

@app.command()
def format(path: str, single: bool = False):
    image = Image.open(path)
    exif = image.getexif()
    creation_time = exif.get(306)

    print(f'Behold! A photo 🙇‍♂️')
    imgcat(open(path))

    if creation_time is None:
        print(f'Date data seems to be missing 🤔')
        creation_time = promptForCustomDate()
    else:
        date = datetime.datetime.strptime(creation_time, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')

        print(f'Photo was taken on {date} 📸')

    tags = promptForTags();

    filename = formatFilename(date, tags);

    final_answers = finalConfirmation(filename)

    filename = filename if final_answers['confirm'] else final_answers['modify']

    print(f'Here you go, the final filename: {filename}')

    return filename

if __name__ == "__main__":
    app()