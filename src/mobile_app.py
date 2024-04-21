#import kivy
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.widget import Widget

KV = '''
MDBoxLayout:
    orientation:"vertical"

    MDTopAppBar:
        title: "Mouse Trap"

    MDTextField:
        adaptive_height:True
        multiline: False
        hint_text: "Enter Trap IP to connect!"

    MDBoxLayout:
        MDLabel:
            text:"Traps go here"
'''

class MobileApp(MDApp):
    def build(self):
        return Builder.load_string(KV)
    
MobileApp().run()