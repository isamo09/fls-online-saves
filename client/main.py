import requests
import os
import json
from datetime import datetime
import zipfile
import webbrowser

SERVER_URL = "https://fsl.pythonanywhere.com"
CONFIG_FILE = "client_config.json"
user_name = os.getlogin()
FSL_dir = f"C:\\Users\\{user_name}\\AppData\\Roaming\\FSL"
data_path = f"{FSL_dir}/data.json"
allov_print = False


def start():
    url = "steam://rungameid/271590"
    webbrowser.open(url)


def search_fsl():
    user_name = os.getlogin()
    FSL_dir = f"C:\\Users\\{user_name}\\AppData\\Roaming\\FSL"
    print(FSL_dir)


def get_credentials():
    login = input("Enter your login: ")
    password = input("Enter your password: ")
    return login, password


def authenticate(login, password):
    response = requests.post(f"{SERVER_URL}/auth", json={"login": login, "password": password})
    if response.status_code in [200, 201]:
        save_value(CONFIG_FILE, "active_slot", 1)
        return response.json().get("access_key")
    else:
        print(f"Error: {response.json().get("error")}")
        return None


def logout():
    save_value(CONFIG_FILE, "access_key", None)


def load_client_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}


def save_client_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)


def save_value(file, key, value):
    try:
        with open(file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[key] = value
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)


def read_value(file, key):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

    try:
        with open(file, "r") as f:
            data = json.load(f)
            if key not in data:
                data[key] = None

            return data[key]
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")
        return None


def rm_local_save():
    try:
        os.remove(f"{FSL_dir}/save_char0001.pso")
    except:
        pass
    try:
        os.remove(f"{FSL_dir}/save_char0002.pso")
    except:
        pass
    try:
        os.remove(f"{FSL_dir}/save_default0000.pso")
    except:
        pass
    try:
        f"{FSL_dir}/{read_value(CONFIG_FILE, 'active_slot')}.zip"
    except:
        pass


def download_latest():
    file_path = os.path.join(FSL_dir, "save_default0000.pso")
    file_mod_time = os.path.getmtime(file_path)
    file_mod_date = datetime.fromtimestamp(file_mod_time)
    save_dates = {key: datetime.strptime(value, "%Y-%m-%d %H:%M:%S") for key, value in get_info().items()}
    save_dates["save_default0000"] = file_mod_date
    max_key = max(save_dates, key=save_dates.get)
    max_date = save_dates[max_key]
    if max_date == file_mod_date:
        upload_save()
    else:
        download_save(max_key)


def download_save(slot_s):
    if not slot_s:
        slot_s = read_value(CONFIG_FILE, "active_slot")
    rm_local_save()
    payload = {
        "access_key": f"{read_value(CONFIG_FILE, "access_key")}"
    }
    full_url = f"{SERVER_URL}/save/download/{slot_s}"

    response = requests.post(full_url, json=payload)
    os.makedirs(FSL_dir, exist_ok=True)
    if response.status_code == 200:
        file_content = response.content
        full_path = f"{FSL_dir}/{slot_s}.zip"

        # Сохранение zip файла
        with open(full_path, "wb") as file:
            file.write(file_content)

        # Разархивирование zip файла
        with zipfile.ZipFile(full_path, "r") as zip_ref:
            zip_ref.extractall(FSL_dir)

        # Удаление zip файла
        os.remove(full_path)

        print(f"Сохранение {slot_s} успешно загружено и разархивировано в {FSL_dir}")
    else:
        print(f"Ошибка при загрузке сохранения: {response.text}")
    slot_s = None


def upload_save():
    files_to_zip = [
        "save_char0001.pso",
        "save_char0002.pso",
        "save_default0000.pso"
    ]

    default_save_path = os.path.join(FSL_dir, "save_default0000.pso")
    if not os.path.exists(default_save_path):
        print("Файл save_default0000.pso не найден. Загрузка сохранений не будет выполнена.")
        return

    zip_filename = f"{read_value(CONFIG_FILE, "active_slot")}.zip"
    zip_filepath = os.path.join(FSL_dir, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        for file_name in files_to_zip:
            file_path = os.path.join(FSL_dir, file_name)
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
            else:
                print(f"Файл {file_name} не найден в {FSL_dir} и будет пропущен")

    with open(zip_filepath, "rb") as file:
        file_content = file.read()

    payload = {
        "access_key": f"{read_value(CONFIG_FILE, "access_key")}"
    }
    files = {
        "file": (zip_filename, file_content, "application/zip")
    }
    full_url = f"{SERVER_URL}/save/upload/{read_value(CONFIG_FILE, "active_slot")}"

    response = requests.post(full_url, data=payload, files=files)

    os.remove(zip_filepath)

    if response.status_code == 200:
        print(f"Сохранение из ячейки {read_value(CONFIG_FILE, "active_slot")} успешно загружено на сервер")
    else:
        print(f"Ошибка при загрузке сохранения: {response.text}")


def delete_save():
    payload = {
        "access_key": f"{read_value(CONFIG_FILE, "access_key")}"
    }
    full_url = f"{SERVER_URL}/save/delite/{read_value(CONFIG_FILE, "active_slot")}"

    response = requests.post(full_url, json=payload)
    if response.status_code == 200:
        print(f"successful deletion of save {read_value(CONFIG_FILE, "active_slot")}")
    else:
        print(f"error: {response.text}")


def get_status():
    payload = {
        "access_key": f"{read_value(CONFIG_FILE, "access_key")}"
    }
    print(payload)
    full_url = f"{SERVER_URL}/status"

    response = requests.post(full_url, json=payload)
    if response.status_code == 200:
        print(f"successful {response.text}")

    elif response.status_code == 401:
        save_value(CONFIG_FILE, "access_key", None)
        print("Error auth")
    else:
        print(f"error: {response.text}")


def get_info(prints=None):
    payload = {
        "access_key": f"{read_value(CONFIG_FILE, "access_key")}"
    }
    full_url = f"{SERVER_URL}/info"

    response = requests.post(full_url, json=payload)
    if response.status_code == 200:
        json_data = response.json()
        save_1 = json_data.get("save 1")
        save_2 = json_data.get("save 2")
        save_3 = json_data.get("save 3")
        if prints:

            print(f"save 1: {save_1}")
            print(f"save 2: {save_2}")
            print(f"save 3: {save_3}")
        return json_data
    elif response.status_code == 401:
        save_value(CONFIG_FILE, "access_key", None)
        print("Error auth")
    else:
        print(f"error: {response.text}")


def main():
    search_fsl()
    get_status()
    get_info()
    config = load_client_config()
    access_key = config.get("access_key")

    if not access_key:
        login, password = get_credentials()
        access_key = authenticate(login, password)

        if access_key:
            config["access_key"] = access_key
            save_client_config(config)
            print(f"Authenticated successfully. Your access key: {access_key}")
        else:
            print("Authentication failed.")
    else:
        print(f"Already authenticated. Your access key: {access_key}")

    print("\nWaiting for commands... print help for help")
    while True:
        command = input(">>>").strip().lower().split(" ")
        if command[0] == "exit":
            print("Exiting...")
            break
        elif command[0] == "select":
            try:
                slot = int(command[1])
            except TypeError and IndexError:
                print(f"uncorrected")
                slot = int(input("slot (1 - 3) >>"))
                if slot not in [1, 2, 3]:
                    print("allow slots 1, 2, 3")
                else:
                    save_value(CONFIG_FILE, "active_slot", slot)

            if slot not in [1, 2, 3]:
                print("allow slots 1, 2, 3")
            else:
                save_value(CONFIG_FILE, "active_slot", slot)
                print(f"selected slot {slot}")

        elif command[0] == "help":
            print("commands: \n"
                  "- help\n"
                  "- status: get status from server\n"
                  "- info\n"
                  f"- select: specify slot, selected slot: {read_value(CONFIG_FILE, "active_slot")}\n"
                  "- download: to download selected save from server\n"
                  "- download_latest: will load the latest save from the server\n"
                  "- upload: to upload selected save from server\n"
                  "- delete: to delete save from the server\n"
                  "- logout\n"
                  "- exit\n"
                  )

        elif command[0] == "start":
            start()

        elif command[0] == "status":
            try:
                get_status()
            except:
                print("error")

        elif command[0] == "download":
            try:
                download_save(read_value(CONFIG_FILE, "active_slot"))
            except:
                print("fall download")

        elif command[0] == "download_latest":
            try:
                download_latest()
            except:
                print("fall download")

        elif command[0] == "upload":
            try:
                upload_save()
            except:
                print("fall upload")

        elif command[0] == "info":
            get_info(True)

        elif command[0] == "delete":
            if not read_value(CONFIG_FILE, "active_slot"):
                print("slot not selected, print select to select slot")
            else:
                if input(f"do you really want to delete the save {read_value(CONFIG_FILE, "active_slot")}?\n"
                         f"print yes to continue >>") in {"Y", "y", "YES", "yes", "Yes"}:
                    try:
                        delete_save()
                        print("deletion complited")
                    except:
                        print("error to deletion")

                else:
                    print("deletion canceled")

        elif command[0] == "logout":
            logout()
            login, password = get_credentials()
            access_key = authenticate(login, password)
            if access_key:
                config["access_key"] = access_key
                save_client_config(config)
                print(f"Authenticated successfully. Your access key: {access_key}")
            else:
                print("Authentication failed.")
        else:
            print(f"not command \"{command[0]}\"\n"
                  f"help to viev command list")


if __name__ == "__main__":
    main()
