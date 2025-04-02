from typing import Final

EXIT_NUMBER: Final[int] = 0
BACK_STRING: Final[str] = 'back'

def is_digit_and_go_back(value):
    return value.isdigit() and int(value) == EXIT_NUMBER


def handle_user_url_input(service):
    return input(f'Enter the {service} URL ({EXIT_NUMBER} to go back): ')


def is_valid_option_selected(option_selected, dict_size):
    if (option_selected.isdigit() and int(option_selected) < dict_size) or option_selected in ('all', 'back'):
        return True

    return False


def validate_return_user_input_choose(dict_size):
    option_selected = input(
        f'\nEnter the number corresponding to the file (or all to add everything or {BACK_STRING} to go back): ')
    valid_option = is_valid_option_selected(option_selected, dict_size)

    while not valid_option:
        option_selected = input('Incorrect option, choose a valid option: ')

        if (is_valid_option_selected(option_selected, dict_size)):
            valid_option = True

    return option_selected
