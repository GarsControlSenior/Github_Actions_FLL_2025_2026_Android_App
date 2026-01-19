from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.utils import platform
from jnius import autoclass

class MainApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        
        # Ein Button, der die Logik startet
        btn = Button(text="Kamera starten", size_hint=(1, 0.2))
        btn.bind(on_press=self.manage_camera_start)
        
        self.layout.add_widget(btn)
        return self.layout

    def manage_camera_start(self, instance):
        """Prüft Berechtigungen und startet die Kamera oder fragt nach Rechten."""
        if platform == 'android':
            from android.permissions import check_permission, request_permissions, Permission
            
            # Liste der benötigten Rechte
            perms = [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
            
            # Prüfen, ob alle Rechte bereits gewährt wurden
            is_granted = all([check_permission(p) for p in perms])
            
            if is_granted:
                # Wenn wir die Rechte schon haben -> Kamera direkt aufrufen
                self.open_camera()
            else:
                # Wenn nicht -> erneut nachfragen
                request_permissions(perms, callback=self.on_permissions_result)
        else:
            print("Kamera-Feature nur auf Android verfügbar.")

    def on_permissions_result(self, permissions, grants):
        """Wird aufgerufen, nachdem der Nutzer auf 'Erlauben' oder 'Ablehnen' geklickt hat."""
        if all(grants):
            # Nutzer hat diesmal zugestimmt
            self.open_camera()
        else:
            # Nutzer hat wieder abgelehnt
            print("Berechtigung verweigert. Kamera kann nicht geöffnet werden.")

    def open_camera(self):
        """Der eigentliche Android-Aufruf für die Kamera."""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            MediaStore = autoclass('android.provider.MediaStore')

            activity = PythonActivity.mActivity
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            
            if intent.resolveActivity(activity.getPackageManager()) is not None:
                activity.startActivity(intent)
        except Exception as e:
            print(f"Fehler: {e}")

if __name__ == "__main__":
    MainApp().run()
