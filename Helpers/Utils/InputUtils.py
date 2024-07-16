def is_digit_and_go_back(link):
    return link.isdigit() and int(link) == 99


def handle_user_url_input(service):
    return input(f"Enter the {service} URL (99 to go back): ")


def is_valid_option_chose(option_chose, dict_size):
    if (option_chose.isdigit() and int(option_chose) < dict_size) or option_chose in ('all', 'back'):
        return True

    return False


def validate_return_user_input_choose(dict_size):
    option_chose = input(
        "\nEnter the number corresponding to the file (or all or back): ")
    valid_option = is_valid_option_chose(option_chose, dict_size)

    while not valid_option:
        option_chose = input("Incorrect option, choose a valid option: ")

        if (is_valid_option_chose(option_chose, dict_size)):
            valid_option = True

    return option_chose
