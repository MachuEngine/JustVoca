import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Hello, Flet!"))
    page.update()

ft.app(target=main, port=8099, view=ft.AppView.WEB_BROWSER, host="0.0.0.0")