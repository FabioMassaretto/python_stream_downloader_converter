def is_digit_and_go_back(link):
    return link.isdigit() and int(link) == 99


def handle_user_url_input(service):
    return input(f"Enter the {service} URL (99 to go back): ")
