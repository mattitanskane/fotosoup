# -*- coding: utf-8 -*-

import pprint
from PyInquirer import prompt
from imgcat import imgcat 
from prompt_toolkit.validation import Validator, ValidationError
from PIL import Image
import datetime
import regex
import typer
import configparser
import os
import send2trash
import shutil
from pathlib import Path

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

def promp_for_custom_date():
    date_questions = [
        {
            'type': 'input',
            'name': 'date',
            'message': 'Please provide a date in format YYYY-MM-DD:',
            'default': '',
            'validate': DateValidator,
        }
    ]

    date_answers = prompt(date_questions)
    return date_answers["date"]

def prompt_for_tags():
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


def format_filename(creation_time, tags, filetype):
    return creation_time + "-" + tags + '.' + filetype.lower()

def final_confirmation(filename):
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

def init_config():
    config_file = Path("./fotosoup.ini")

    if config_file.is_file():
        print('Using existing config file.')

        config = configparser.ConfigParser()
        config.read('fotosoup.ini')

        return True

    def config_file_exists(answers):
        # PyInquirer seems to need a function and a boolean is not enough
        return config_file.is_file()

    default_input = './input/'
    default_output = './output/'

    config_questions = [
            {
                'type': 'confirm',
                'name': 'config_missing',
                'message': f'Config file missing. Use default config?',
                'when': not config_file_exists
            },
            {
                'type': 'input',
                'name': 'input_directory',
                'message': 'Path for input directory:',
                'default': default_input,
                'when': lambda answers: not answers['config_missing'],
            },
            {
                'type': 'input',
                'name': 'output_directory',
                'message': 'Path for output directory:',
                'default': default_output,
                'when': lambda answers: not answers['config_missing'],
            }
        ]
    config_answers = prompt(config_questions)

    input_directory = config_answers['input_directory'] if not config_answers['config_missing'] else default_input
    output_directory = config_answers['output_directory'] if not config_answers['config_missing'] else default_output

    config = configparser.ConfigParser()
    config['DEFAULT'] = {'InputDirectory': input_directory,
                        'OutputDirectory': output_directory}
    with open('fotosoup.ini', 'w') as configfile:
        config.write(configfile)

    return True

def get_input_path_from_config():
    config_file = Path("./fotosoup.ini")

    if config_file.is_file():
        config = configparser.ConfigParser()
        config.read('fotosoup.ini')

        return config['DEFAULT']['inputdirectory']

    return False

def get_output_path_from_config():
    config_file = Path("./fotosoup.ini")

    if config_file.is_file():
        config = configparser.ConfigParser()
        config.read('fotosoup.ini')

        return config['DEFAULT']['outputdirectory']

    return False

def valid_filetype(file):
    file = file.lower()

    if '.jpg' in file:
        return True
        
    if '.jpeg' in file:
        return True
        
    if '.png' in file:
        return True

    return False

@app.command()
def format(path: str = ''):
    init_config()

    input_directory_path = get_input_path_from_config()
    output_directory_path = get_output_path_from_config()

    print(input_directory_path)
    
    # to store files in a list
    filelist = []
    
    # dirs=directories
    for (root, dirs, file) in os.walk(input_directory_path):
        for image in file:
            if valid_filetype(image):
                filelist.append(image)

    print(filelist)

    index = 0
    for filename in filelist:
        filepath = input_directory_path + filename
        image = Image.open(filepath)
        image_filetype = image.format
        exif = image.getexif()
        creation_time = exif.get(306)

        # print(f'Behold! A photo 🙇‍♂️')
        imgcat(open(filepath))

        if creation_time is None:
            print(f'Date data seems to be missing 🤔')
            date = promp_for_custom_date()
        else:
            date = datetime.datetime.strptime(creation_time, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')

            print(f'Photo was taken on {date} 📸')

        tags = prompt_for_tags();

        formatted_filename = format_filename(date, tags, image_filetype);

        final_answers = final_confirmation(formatted_filename)

        formatted_filename = formatted_filename if final_answers['confirm'] else final_answers['modify']

        print(f'Here you go, the final filename: {formatted_filename}')

        # TODO: Move file to output directory
        # TODO: Trash original from input directory

        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)
        
        shutil.move(filepath, output_directory_path + formatted_filename)

        index = index + 1
        if index is not len(filelist):            
            print(f'>')
            print(f'>')
            print(f'> Next photo coming up')
            print(f'>')
            print(f'>')

        else:
            print(f'>')
            print(f'>')
            print(f'> That was the last photo!')
            print(f'>')
            print(f'>')
    
    print('\n')
    print('Bye! 👋')

    return True

if __name__ == "__main__":
    app()