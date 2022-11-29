# -*- coding: utf-8 -*-

import pprint
import datetime
import regex
import typer
import configparser
import os
import shutil
from send2trash import send2trash
from PyInquirer import prompt
from imgcat import imgcat 
from prompt_toolkit.validation import Validator, ValidationError
from pathlib import Path
from PIL import Image
from hashlib import blake2b

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
        ok = regex.match('^[0-9-]*$', document.text)
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

def prompt_for_action():
    questions = [
        {
            'type': 'expand',
            'name': 'action',
            'message': 'What would you like to do?',
            'default': '',
            'choices': [
                {
                    'key': 'y',
                    'name': 'Rename current image',
                    'value': 'rename'
                },
                {
                    'key': 'n',
                    'name': 'Skip this image and move to the next one',
                    'value': 'skip'
                },
                {
                    'key': 'd',
                    'name': 'Delete this image',
                    'value': 'delete'
                },
            ]
        },
    ]

    answers = prompt(questions)

    return answers["action"]

def prompt_for_tags():
    questions = [
        {
            'type': 'input',
            'name': 'tags',
            'message': 'Please enter a space separated list of tags:',
            'default': '',
            'validate': TagValidator,
            'filter': lambda val: val.strip().lower().replace(' ', '-'),
        }
    ]

    answers = prompt(questions)

    return answers["tags"]

def format_filename(creation_time, tags, filetype, include_extension = True, is_duplicate = False):
    if not include_extension:
        return creation_time + "-" + tags

    if is_duplicate:
        return creation_time + "-" + tags + '#' +  blake2b(digest_size=10, salt=os.urandom(10)).hexdigest() + '.' + filetype.lower() 

    return creation_time + "-" + tags + '.' + filetype.lower()

def final_confirmation(filename, filename_without_extension):
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
            'default': filename_without_extension,
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

def format_filetype(file_extension):
    return '.' + file_extension.lower()

@app.command()
def format(input: str = ''):
    init_config()

    input_directory_path = input if input else get_input_path_from_config()
    output_directory_path = get_output_path_from_config()
    
    # to store files in a list
    filelist = []

    # TODO: Gentle crl-c exit
    
    # dirs=directories
    for (root, dirs, file) in os.walk(input_directory_path):
        for image in file:
            if valid_filetype(image):
                filelist.append(image)

    if not filelist:
        print(f'\nNo files found in input directory 🤔 Check fotosoup.ini for directory paths.')
        return

    index = 0
    for filename in filelist:
        filepath = os.path.join(input_directory_path, filename)
        image = Image.open(filepath)

        image_filetype = image.format
        exif = image.getexif()
        creation_time = exif.get(306)

        if creation_time is None:
            print(f'This image is missing its Exif date information ❓')
        else:
            date = datetime.datetime.strptime(creation_time, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d')
            print(f'This image was taken on {date} 📸')
            
        imgcat(open(filepath))

        action = prompt_for_action()

        if action == 'skip':
            # Go to next image
            continue

        if action == 'delete':
            # Delete current image
            send2trash(filepath)
            # Go to next image
            continue

        if action == 'rename':
            # Continue with current image
            pass

        if creation_time is None:
            date = promp_for_custom_date()
            
        tags = prompt_for_tags()

        formatted_filename_without_extension = format_filename(date, tags, image_filetype, False);
        formatted_filename = format_filename(date, tags, image_filetype);

        final_answers = final_confirmation(formatted_filename, formatted_filename_without_extension)

        formatted_filename = formatted_filename if final_answers['confirm'] else final_answers['modify'] + format_filetype(image_filetype)

        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)

        if os.path.exists(output_directory_path + formatted_filename):
            print('Found a file with the same name, adding 10 digit hash at the end of the filename.')
            print('New filename: ' + format_filename(date, tags, image_filetype, True, True))
            shutil.move(filepath, output_directory_path + format_filename(date, tags, image_filetype, True, True))

        else:
            print(f'Here you go, the final filename: {formatted_filename}')
            shutil.move(filepath, output_directory_path + formatted_filename)
        
        # TODO: Easy deletion or skip

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