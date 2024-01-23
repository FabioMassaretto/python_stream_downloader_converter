import datetime

# Pathway to file that is collecting the version list.
text_file_location = './version.txt'

# Opens and writes the version.txt file.
TODO_file = open(text_file_location, 'w+')

patch = f"{ str(datetime.datetime.today().microsecond) }"
version = f"{ str(datetime.datetime.today().year) }.{ str(datetime.datetime.today().month) }.{ str(datetime.datetime.today().day) }[{patch}]"

# Prints the last date modified for convenience. 
TODO_file.write(f"version={version}")
# Closes the TODO_file
TODO_file.close()
