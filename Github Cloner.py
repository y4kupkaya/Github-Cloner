import json
import logging
import os
import pathlib
import re
import sys

import flet as f
import git
import requests

logging.basicConfig(level=logging.WARNING)


c1 = f.Checkbox(label=".git Klasörlerini Sil", value=True)
c2 = f.Checkbox(label="İşlem Bitince Klasörü Aç", value=True)
len_repos_label = f.Text("Toplam {} repo bulundu. Klonlanıyor...")


def get_username_and_repo_name(github_repo_link):
    pattern = r"^https:\/\/github.com\/([^\/]+)\/([^\/]+)"
    result = re.search(pattern, github_repo_link)
    if result:
        username = result.group(1)
        repo_name = result.group(2)
        return (username, repo_name)
    else:
        return None


def get_repos(username: str):
    repos = []
    try:
        get = requests.get(f"https://api.github.com/users/{username}/repos")
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
    ):
        print("Error: ConnectionError")
        return None

    json_data = json.loads(get.text)
    for i in json_data:
        url = "https://" + str(i["git_url"]).replace("git://", "") + "\n"
        repos.append(url.replace("\n", ""))
    return repos


def git_folder_deleter(path: str):
    """Verilen klasörün alt klasörlerindeki .git klasörlerini siler"""
    for root, dirs, files in os.walk(path):
        for i in dirs:
            if i == ".git":
                os.system(f"rmdir /S /Q {root}\\{i}")
                print(f"Deleted: {root}\\{i}")
                print("-" * 50)


def git_clone(repositoryes: list, path: str = "repositoryes", page: f.Page = None):
    suscess = 0
    error = 0
    button_list = []
    if not os.path.exists(path):
        os.mkdir(path)

    os.chdir(path)
    username, _ = get_username_and_repo_name(repositoryes[0])

    if username is None:
        print("Error: Username not found")
        return None

    if not os.path.exists(f"{username}"):
        os.mkdir(f"{username}")
    os.chdir(f"{username}")

    for i in repositoryes:
        i: str
        try:
            __, repo_name = get_username_and_repo_name(i)
            git.Repo.clone_from(i, f"{repo_name.replace('.git', '')}")
            cloned_path = os.getcwd() + "\\" + repo_name.replace(".git", "")
            suscess += 1
            print(f"Cloned: {i.split('/')[-1].replace('.git', '')}")
            print(f"Path: {cloned_path}")
            print("-" * 50)

            if page is None:
                return
            clnd_path = (
                str(path)
                + "\\"
                + str(username)
                + "\\"
                + str(repo_name).replace(".git", "")
            )
            button = f.TextButton(
                f"{i.split('/')[-1].replace('.git', '')}",
                on_click=lambda _: os.startfile(clnd_path),
                tooltip="Klasörü Aç",
            )
            button_list.append(button)
            print(button_list)
            lv = f.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)
            lv.controls = button_list
            if len(button_list) == 1:
                page.add(lv)
            y = 674
            page.window_height = y
            page.update()
            if c1.value:
                git_folder_deleter(cloned_path)

        except Exception as e:
            error += 1
            print(e)
    print(f"Total: {suscess + error}\nSuscess: {suscess}\nError: {error}")
    if c2.value:
        os.system(f"start {os.getcwd()}")
    len_repos_label.value = f"{username} kullanıcısının repoları:"
    page.update()
    return suscess, error


def main(page: f.Page):
    page.title = "Github Clone"
    page.bgcolor = "dark"
    page.padding = 10
    page.spacing = 10
    x = 443
    y = 242
    page.window_width = x
    page.window_height = y
    page.theme_mode = "dark"
    page.window_resizable = True

    def flet_git_clone(e):
        if userame_field.value == "":
            userame_field.error_text = "Lütfen bir kullanıcı adı girin!"
            page.update()
            return
        user_repos = get_repos(userame_field.value)
        if user_repos is None:
            userame_field.error_text = "Kullanıcı adı bulunamadı!"
            page.update()
        else:
            userame_field.error_text = None
            len_repos_label.value = (
                f"Toplam {len(user_repos)} repo bulundu. Klonlanıyor..."
            )
            page.add(len_repos_label)
            page.update()
            git_clone(user_repos, output_path_field.value, page)

    def check_path(e):
        path = output_path_field.value
        if path == "":
            output_path_field.error_text = "Lütfen bir dizin seçin!"
            page.update()
        else:
            if os.path.exists(path):
                output_path_field.error_text = None
                page.update()
            else:
                if path == str(pathlib.Path.home() / "Documents"):
                    os.mkdir(path)
                    output_path_field.error_text = None
                    page.update()
                else:
                    output_path_field.error_text = "Dizin bulunamadı!"
                page.update()

    def get_directory_result(e: f.FilePickerResultEvent):
        if e.path:
            output_path_field.value = e.path
            output_path_field.error_text = None
            output_path_field.update()
            page.update()

    get_directory_dialog = f.FilePicker(on_result=get_directory_result)
    output_path_field = f.TextField(
        value=pathlib.Path.home() / "Documents",
        width=350,
        multiline=False,
        dense=True,
        on_change=check_path,
        label="Çıktı Yolu",
    )
    # Sayfaya ekle
    page.overlay.extend([get_directory_dialog])
    output_path_field_content_icon = f.IconButton(
        f.icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_dialog.get_directory_path(
            dialog_title="Çıktı Yolu Seçin",
            initial_directory=pathlib.Path.home() / "Documents",
        ),
        tooltip="Çıktı Klasörü Seçin",
    )
    userame_field = f.TextField(
        hint_text="Kullanıcı adını giriniz.",
        width=350,
        multiline=False,
        dense=True,
        label="Github Username",
    )
    repos_clone_icon_button = f.IconButton(
        f.icons.GITE,
        on_click=flet_git_clone,
        tooltip="Tüm Repoları Klonla",
    )
    repos_clone_icon_button = f.Container(
        f.Column(
            [
                f.Image(
                    src_base64="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",
                    width=40,
                    height=40,
                ),
                f.Text("Klonla", size=12),
            ],
            alignment=f.MainAxisAlignment.CENTER,
        ),
        on_click=flet_git_clone,
        tooltip="Tüm Repoları Klonla",
        alignment=f.alignment.center,
    )
    page.add()
    page.add(
        f.Container(
            content=f.Column(
                controls=[
                    # output_path_text,
                    f.Row(
                        [userame_field, repos_clone_icon_button],
                        alignment=f.MainAxisAlignment.CENTER,
                    ),
                ],
                wrap=True,
                alignment=f.MainAxisAlignment.CENTER,
            ),
            alignment=f.alignment.center,
        )
    )
    page.add(
        f.Container(
            content=f.Column(
                controls=[
                    # output_path_text,
                    f.Row(
                        [output_path_field, output_path_field_content_icon],
                        alignment=f.MainAxisAlignment.CENTER,
                    ),
                ],
                wrap=True,
                alignment=f.MainAxisAlignment.CENTER,
            ),
            alignment=f.alignment.center,
        )
    )
    page.add(f.Row([c1, c2], alignment=f.MainAxisAlignment.CENTER))


if __name__ == "__main__":
    f.app(
        main,
        name="GitCloner",
    )
