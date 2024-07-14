def build_main_title(name: str):
    name_len = len(name)
    print('\n')
    print(f"|{'-'*int(52+name_len)}|")
    print(f"|{' '*int(25)} {name} {' '*int(25)}|")
    print(f"|{'-'*int(52+name_len)}|", end='\n')

# sub_name_len: int = 0


def build_sub_title(sub_name: str):
    global sub_name_len
    sub_name_len = len(sub_name)
    print('\n')
    print(f"{'#'*int(26)} {sub_name} {'#'*int(26)}")


def build_ending_sub_title():
    print(f"{'#'*int(54+sub_name_len)}")
