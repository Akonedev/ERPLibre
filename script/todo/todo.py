#!/usr/bin/env python

import getpass
import json
import logging
import os
import subprocess
import tkinter as tk
from tkinter import filedialog

import click
import openai
from pykeepass import PyKeePass

# TODO implement urwid to improve text user interface
# import urwid
_logger = logging.getLogger(__name__)

CONFIG_FILE = "./script/todo/todo.json"
CONFIG_OVERRIDE_FILE = "./script/todo/todo_override.json"
LOGO_ASCII_FILE = "./script/todo/logo_ascii.txt"


class TODO:
    def __init__(self):
        self.kdbx = None

    def run(self):
        with open(LOGO_ASCII_FILE) as my_file:
            print(my_file.read())
        print("Ouverture de TODO en cours ...")
        print("🤖 => Entre tes directives par son chiffre et fait Entrée!")
        help_info = """Commande :
[1] Question
[2] Execute
[3] Fork - Ouvre TODO 🤖 dans une nouvelle tabulation
[0] Quitter
"""
        # [3] install
        while True:
            status = click.prompt(help_info)
            print()
            if status == "0":
                break
            elif status == "1":
                self.execute_prompt_ia()
            elif status == "2":
                self.prompt_execute()
            elif status == "3":
                cmd = (
                    f"gnome-terminal --tab -- bash -c 'source"
                    f" ./.venv/bin/activate;make todo'"
                )
                self.executer_commande_live(cmd)
            # elif status == "3" or status == "install":
            #     print("install")
            else:
                print("Commande non trouvée 🤖!")

        print(status)
        # manipuler()

    def get_kdbx(self):
        if self.kdbx:
            return self.kdbx
        # Open file
        chemin_fichier_kdbx = self.get_config(["kdbx", "path"])
        if not chemin_fichier_kdbx:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            chemin_fichier_kdbx = filedialog.askopenfilename(
                title="Select a File",
                filetypes=(("KeepassX files", "*.kdbx"),),
            )
        if not chemin_fichier_kdbx:
            _logger.error(f"KDBX is not configured, please fill {CONFIG_FILE}")
            return

        mot_de_passe_kdbx = self.get_config(["kdbx", "password"])
        if not mot_de_passe_kdbx:
            mot_de_passe_kdbx = getpass.getpass(
                prompt="Entrez votre mot de passe : "
            )

        kp = PyKeePass(chemin_fichier_kdbx, password=mot_de_passe_kdbx)

        if kp:
            self.kdbx = kp
        return kp

    def get_config(self, lst_params):
        # Open file
        config_file = CONFIG_FILE
        if os.path.exists(CONFIG_OVERRIDE_FILE):
            config_file = CONFIG_OVERRIDE_FILE

        with open(config_file) as cfg:
            dct_data = json.load(cfg)
            for param in lst_params:
                try:
                    dct_data = dct_data[param]
                except KeyError:
                    _logger.error(
                        f"KeyError on file {config_file} with keys"
                        f" {lst_params}"
                    )
                    return
        return dct_data

    def execute_prompt_ia(self):
        while True:
            help_info = """Commande :
[0] Retour
Écrit moi ta question """
            status = click.prompt(help_info)
            print()
            if status == "0":
                return
            kp = self.get_kdbx()
            if not kp:
                return
            nom_configuration = self.get_config(
                ["kdbx_config", "openai", "kdbx_key"]
            )
            entry = kp.find_entries_by_title(nom_configuration, first=True)

            client = openai.OpenAI(api_key=entry.password)
            prompt_update = status
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_update}],
            )

            print(completion.choices[0].message.content)
            print()

    def prompt_execute(self):
        help_info = """Commande :
[1] Gérer une instance
[2] Fonction - Démonstration des fonctions développées
[0] Retour
"""
        while True:
            status = click.prompt(help_info)
            print()
            if status == "0":
                return
            elif status == "1":
                status = self.prompt_execute_instance()
                if status is not False:
                    return
            elif status == "2":
                status = self.prompt_execute_fonction()
                if status is not False:
                    return
            else:
                print("Commande non trouvée 🤖!")

    def execute_from_configuration(
        self, dct_instance, exec_run_db=False, ignore_makefile=False
    ):
        # exec_run_db need argument database
        kdbx_key = dct_instance.get("kdbx_key")
        odoo_user = dct_instance.get("user")
        odoo_password = dct_instance.get("password")

        if kdbx_key:
            extra_cmd_web_login = self.kdbx_get_extra_command_user(kdbx_key)
        elif odoo_user and odoo_password:
            extra_cmd_web_login = (
                f" --default_email_auth {odoo_user} --default_password_auth"
                f" '{odoo_password}'"
            )
        else:
            extra_cmd_web_login = ""

        makefile_cmd = dct_instance.get("makefile_cmd")
        if makefile_cmd and not ignore_makefile:
            self.executer_commande_live(f"make {makefile_cmd}")

        if exec_run_db:
            db_name = dct_instance.get("database")
            self.prompt_execute_selenium_and_run_db(
                db_name, extra_cmd_web_login=extra_cmd_web_login
            )

        command = dct_instance.get("command")
        if command:
            self.prompt_execute_selenium(
                command=command, extra_cmd_web_login=extra_cmd_web_login
            )

    def fill_help_info(self, lst_instance):
        help_info = "Commande :\n"
        help_end = "[0] Retour\n"
        for i, dct_instance in enumerate(lst_instance):

            help_info += (
                f"[{i + 1}] " + dct_instance["prompt_description"] + "\n"
            )
        help_info += help_end
        return help_info

    def prompt_execute_instance(self):
        lst_instance = self.get_config(["instance"])
        help_info = self.fill_help_info(lst_instance)

        while True:
            status = click.prompt(help_info)
            print()
            if status == "0":
                return False
            else:
                cmd_no_found = True
                try:
                    int_cmd = int(status)
                    if 0 < int_cmd <= len(lst_instance):
                        cmd_no_found = False
                        status = click.confirm(
                            "Voulez-vous une nouvelle instance?"
                        )
                        dct_instance = lst_instance[int_cmd - 1]
                        self.execute_from_configuration(
                            dct_instance,
                            exec_run_db=True,
                            ignore_makefile=not bool(status),
                        )
                except ValueError:
                    pass
                if cmd_no_found:
                    print("Commande non trouvée 🤖!")

    def prompt_execute_fonction(self):
        lst_instance = self.get_config(["function"])
        help_info = self.fill_help_info(lst_instance)

        while True:
            status = click.prompt(help_info)
            print()
            if status == "0":
                return False
            else:
                cmd_no_found = True
                try:
                    int_cmd = int(status)
                    if 0 < int_cmd <= len(lst_instance):
                        cmd_no_found = False
                        dct_instance = lst_instance[int_cmd - 1]
                        self.execute_from_configuration(dct_instance)
                except ValueError:
                    pass
                if cmd_no_found:
                    print("Commande non trouvée 🤖!")

    def kdbx_get_extra_command_user(self, kdbx_key):
        lst_value = []
        if kdbx_key:
            kp = self.get_kdbx()
            if not kp:
                return ""
            if type(kdbx_key) is not list:
                lst_kdbx_key = [kdbx_key]
            else:
                lst_kdbx_key = kdbx_key
            for key in lst_kdbx_key:
                entry = kp.find_entries_by_title(key, first=True)
                try:
                    odoo_user = entry.username
                except AttributeError:
                    _logger.error(f"Cannot find username from keys {key}")
                try:
                    odoo_password = entry.password
                except AttributeError:
                    _logger.error(f"Cannot find password from keys {key}")
                lst_value.append(
                    " --default_email_auth"
                    f" {odoo_user} --default_password_auth '{odoo_password}'"
                )
        if len(lst_value) == 0:
            return ""
        elif len(lst_value) == 1:
            return lst_value[0]
        return lst_value

    def prompt_execute_selenium_and_run_db(self, bd, extra_cmd_web_login=""):
        cmd = (
            f'parallel ::: "./run.sh -d {bd}" "sleep'
            f' 3;./script/selenium/web_login.py{extra_cmd_web_login}"'
        )
        self.executer_commande_live(cmd)

    def prompt_execute_selenium(self, command=None, extra_cmd_web_login=""):
        lst_cmd = []
        if not command:
            cmd = "./script/selenium/web_login.py"
        else:
            cmd = command

        if type(extra_cmd_web_login) is list:
            for item in extra_cmd_web_login:
                lst_cmd.append(cmd + item)
        else:
            lst_cmd.append(cmd + extra_cmd_web_login)

        if len(lst_cmd) == 1:
            self.executer_commande_live(lst_cmd[0])
        elif len(lst_cmd) > 1:
            new_cmd = "parallel ::: "
            for i, cmd in enumerate(lst_cmd):
                new_cmd += f' "sleep {1 * i};{cmd}"'
            self.executer_commande_live(new_cmd)

    def executer_commande_live(self, commande):
        """
        Exécute une commande et affiche la sortie en direct.

        Args:
            commande (str): La commande à exécuter (sous forme de chaîne de caractères).
        """
        try:
            process = subprocess.Popen(
                commande,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Désactive la mise en tampon pour la sortie en direct
                universal_newlines=True,  # Pour traiter les sauts de lignes correctement
            )

            while True:
                ligne = process.stdout.readline()
                if not ligne:
                    break
                print(ligne, end="")

            process.wait()  # Attendre la fin du process

            if process.returncode != 0:
                print(
                    "La commande a retourné un code d'erreur :"
                    f" {process.returncode}"
                )

        except FileNotFoundError:
            if "password" in commande:
                print(
                    f"Erreur : La commande '{commande.split(' ')[0]}'[...] n'a"
                    " pas été trouvée."
                )
            else:
                print(
                    f"Erreur : La commande '{commande}' n'a pas été trouvée."
                )
        except Exception as e:
            print(f"Une erreur s'est produite : {e}")


if __name__ == "__main__":
    todo = TODO()
    todo.run()
