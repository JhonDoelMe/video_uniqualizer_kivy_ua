# plyer_test_app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from plyer import filechooser # type: ignore
import os # Додамо os для перевірки шляху

class PlyerTestLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.info_label = Label(text="Натисніть кнопку, щоб обрати папку")
        self.add_widget(self.info_label)

        btn_folder = Button(text="Обрати папку (Plyer Test)")
        btn_folder.bind(on_press=self.select_folder_plyer)
        self.add_widget(btn_folder)

    def select_folder_plyer(self, instance):
        self.info_label.text = "Очікування вибору папки..."
        print("PLYER_TEST_APP: Виклик filechooser.choose_dir...")
        try:
            # Деякі реалізації Plyer можуть не підтримувати filters для choose_dir
            filechooser.choose_dir(on_selection=self.handle_plyer_selection)
        except Exception as e:
            self.info_label.text = f"Помилка виклику Plyer: {str(e)}"
            print(f"PLYER_TEST_APP: Помилка виклику Plyer: {str(e)}")

    def handle_plyer_selection(self, selection):
        # Ця функція буде викликана після того, як користувач зробить вибір у діалозі
        self.info_label.text = f"Plyer повернув: {selection}\nТип результату: {type(selection)}"
        print(f"PLYER_TEST_APP: Отримано вибір: {selection}, Тип: {type(selection)}")

        selected_path = ""
        if selection: # Якщо selection не None і не порожній список/рядок
            if isinstance(selection, list) and len(selection) > 0:
                selected_path = selection[0]
            elif isinstance(selection, str):
                selected_path = selection

        if selected_path and os.path.isdir(selected_path):
            print(f"PLYER_TEST_APP: Обрано коректний шлях до папки: {selected_path}")
            self.info_label.text += f"\nОбрано шлях: {selected_path}"
        elif selected_path: # Якщо шлях є, але це не директорія
             print(f"PLYER_TEST_APP: Обраний шлях НЕ є папкою: {selected_path}")
             self.info_label.text += f"\nПомилка: Обраний шлях '{selected_path}' не є папкою."
        else: # Якщо selection був порожнім або не вдалося витягти шлях
             print(f"PLYER_TEST_APP: Вибір скасовано або шлях порожній.")
             self.info_label.text += f"\nВибір скасовано або шлях не отримано."


class PlyerTestApp(App):
    def build(self):
        return PlyerTestLayout()

if __name__ == '__main__':
    PlyerTestApp().run()