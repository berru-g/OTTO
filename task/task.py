import os
import time
from pyfiglet import Figlet
import winsound
#from termcolor import colored
GREEN = '\033[92m'
PURPLE = '\033[95m'
RESET = '\033[0m'
ROUGE = '\033[31m'
VERT = '\033[32m'
JAUNE = '\033[33m'
BLEU = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
BLANC = '\033[37m'
# Versions claires
CLAIR_NOIR = '\033[90m'
CLAIR_ROUGE = '\033[91m'
CLAIR_VERT = '\033[92m'
CLAIR_JAUNE = '\033[93m'
CLAIR_BLEU = '\033[94m'
CLAIR_MAGENTA = '\033[95m'
CLAIR_CYAN = '\033[96m'
BLANC_BRILLANT = '\033[97m'

f = Figlet(font='slant')
print (f.renderText('Privatask'))
print ('Welcome to the task tool, no ads, no data, just task & you without tracking time.')
#print(CLAIR_NOIR + '###################### more tool in github/berru-g ##############################' + RESET)
print(JAUNE + "Write add and your task & list for looking list & valid or write done & number task." + RESET)
print(CYAN + "add - list - clear - done - record - old-list - quit" + RESET)

tasks = []
    
def print_tasks():
    os.system('cls' if os.name == 'nt' else 'clear')
    print (f.renderText('private task'))
    print(CYAN + 'add - list - clear - done - record - old-list - quit' + RESET)
    for index, task_info in enumerate(tasks, start=1):
        task_status = GREEN + "[x]" if task_info["done"] else CLAIR_ROUGE + "[ ]"
        print(f"{index}. {task_status} {task_info['task']}" + RESET)
        
def record_tasks():
    try:
        with open("tasks.json", "w") as file:
            for task_info in tasks:
                task_status = "done" if task_info["done"] else "not"
                file.write(f"{task_info['task']} ({task_status})\n")
        print(JAUNE + "Liste des tâches enregistrée dans tasks.txt" + RESET)
    except Exception as e:
        print(ROUGE + f"Une erreur s'est produite lors de l'enregistrement des tâches : {e}" + RESET)



def old_list():
    try:
        with open("tasks.json", "r") as file:
            lines = file.readlines()
            tasks.clear()
            for line in lines:
                task, status = line.strip().rsplit("(", 1)
                done = True if "done" in status else False
                task = task.strip()
                tasks.append({"task": task, "done": done})
        print(JAUNE + "Liste des tâches chargée depuis tasks.txt" + RESET)
    except Exception as e:
        print(ROUGE + f"Fichier tasks.txt introuvable. {e}" + RESET)
        

while True:
    user_input = input(": ")

    if user_input.startswith("add "):
        task = user_input[4:]
        tasks.append({"task": task, "done": False})
        print_tasks()
    elif user_input == "record":
        record_tasks()
    elif user_input == "old-list":
        old_list()
    elif user_input == "quit":
        break
    elif user_input == "list":
        print_tasks()
    elif user_input.startswith("done "):
        try:
            task_index = int(user_input[5:]) - 1
            tasks[task_index]["done"] = True
            print(CYAN + "Tâche marquée comme terminée." + RESET)
        except (ValueError, IndexError):
            print(ROUGE + "Invalide. Conservez le format, done suivie du numéro de la tâche à valider." + RESET)
    elif user_input == "clear":
        tasks.clear()
        print(JAUNE + "Historique effacé." + RESET)
    elif user_input == "npm list":
        for i in range(20):
            print(GREEN + "▮" * i, end="\r")
            time.sleep(0.1)
        print(JAUNE + "    +-- learn@7.7.7" + RESET)
        time.sleep(0.1)
        print(JAUNE + "    +-- make@1.0.1" + RESET)
        time.sleep(0.1)
        print(JAUNE + "     -- play@1.2.3" + RESET)
    else:
        print(ROUGE + "Non valide" + RESET)
        winsound.Beep(200, 200)
        winsound.Beep(1000, 200)
