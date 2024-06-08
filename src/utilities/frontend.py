# LAYOUT #
KV='''
BoxLayout:
    orientation: 'vertical'
    
    Label:
        id:             title
        text:           "MouseTrap-Mobile"
        font_size:      40
        pos_hint:       {'center_x': 0.5, 'center_y': 0.5}
        size_hint:      (1, 0.15)
        canvas.before:
            Color:
                rgba:   0,0,0,1
            Rectangle:
                pos:    self.pos
                size:   self.size

    Label:
        id:             Infobar
        text:           "THIS IS THE INFOBAR"
        pos_hint:       {'center_x': 0.5, 'center_y': 0.5}
        size_hint:      (1, 0.05)
        color:          1,1,1,1
        canvas.before:
            Color:
                rgba:   0,0,0,1
            Rectangle:
                pos:    self.pos
                size:   self.size

    TextInput:
        id:                 TextInput
        font_size:          24
        size_hint:          (1, 0.10)
        multiline:          False
        on_text_validate:   app.connect(self.text)

    Label:
        id:             Connection
        text:           "CONNECTION: OFFLINE"
        color:          1,0,0,1
        size_hint:      (1, 0.05)
        canvas.before:
            Color:
                rgba:   0,0,0,1
            Rectangle:
                pos:    self.pos
                size:   self.size

    Label:
        id:             IPV4
        text:           "IPV4: None"
        size_hint:      (1, 0.05)
        canvas.before:
            Color:
                rgba:   0,0,0,1
            Rectangle:
                pos:    self.pos
                size:   self.size

    Label:
        id:             Status
        text:           "STATUS: UNKOWN"
        size_hint:      (1, 0.05)
        canvas.before:
            Color:
                rgba:   0,0,0,1
            Rectangle:
                pos:    self.pos
                size:   self.size

    BoxLayout:
        id:             control
        orientation:    'vertical'
        canvas.before:
            Color:
                rgba:   1,1,1,0.1
            Rectangle:
                pos:    self.pos
                size:   self.size

        BoxLayout:
            id:             controlbuttons
            orientation:    'horizontal'
            size_hint:(1,0.1)
            canvas.before:
                Color:
                    rgba:   1,0,1,0.1
                Rectangle:
                    pos:    self.pos
                    size:   self.size

            Button:
                id:             CloseButton
                text:           "CLOSE"
                on_press:       app.sendCloseR()
                canvas.before:
                    Color:
                        rgba:   0,0,0,1
                    Rectangle:
                        pos:    self.pos
                        size:   self.size
            Button:
                id:             OpenButton
                text:           "OPEN"
                on_press:       app.sendOpenR()
                canvas.before:
                    Color:
                        rgba:   0,0,0,1
                    Rectangle:
                        pos:    self.pos
                        size:   self.size

        Button:
            id:             PhotoButton
            text:           "PHOTO"
            font_size:      24
            size_hint:      (1, 0.10)
            on_press:       app.sendPhotoR()
            canvas.before:
                Color:
                    rgba:   0,0,0,1
                Rectangle:
                    pos:    self.pos
                    size:   self.size
                        
        Image:
            id:             Photo
            source:         "./pics/recv.png"
            canvas.before:
                Color:
                    rgba:   0,0,0,1
                Rectangle:
                    pos:    self.pos
                    size:   self.size
'''