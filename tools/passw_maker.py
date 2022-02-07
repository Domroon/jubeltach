import json
import secrets

def main():
    file_path = input("Please Enter JSON-File Path: ")
    with open(file_path,'r') as file:
        user_list = json.load(file)
    
    for user in user_list:
        user["password"] = secrets.token_urlsafe(6)

    random_file_name = secrets.token_urlsafe(6)
    json.dump(user_list, open(random_file_name, 'w'))


if __name__ == '__main__':
    main()