from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from random import random, uniform, choice

BARRA_ALTURA = 90
EVENTO_DURACION = 20
MINI_SCALE = 2 / 3

# =========================
# BOLA
# =========================
class Bola:
    def __init__(self, parent, x, y, rainbow=False, giant=False, mini=False):
        self.parent = parent
        self.base_size = uniform(25, 60)
        
        # Determinar factor de tamaño inicial
        self.factor_actual = 1.0
        if giant: self.factor_actual = 2.0
        elif mini: self.factor_actual = MINI_SCALE
        
        self.size = self.base_size * self.factor_actual

        self.vx = uniform(-220, 220)
        self.vy = uniform(-220, 220)

        self.rainbow = rainbow
        self.hue = random()
        self.base_color = (uniform(0.3, 1), uniform(0.3, 1), uniform(0.3, 1))

        with parent.canvas:
            self.color = Color(*self.base_color, 1)
            self.circle = Ellipse(size=(self.size, self.size))
            self.border_color = Color(0, 0, 0, 1)
            self.border = Line(width=1)

        # Posicionamiento inicial centrado en el toque
        r = self.size / 2
        self.circle.pos = (x - r, y - r)
        self.actualizar_borde()

    def actualizar_borde(self):
        """ Actualiza la línea negra para que siga al círculo perfectamente """
        x, y = self.circle.pos
        r = self.size / 2
        self.border.circle = (x + r, y + r, r)

    def set_scale(self, nuevo_factor):
        """ Cambia el tamaño sin que la bola 'salte' de posición """
        # Guardamos el centro actual
        centro_x = self.circle.pos[0] + self.size / 2
        centro_y = self.circle.pos[1] + self.size / 2
        
        self.factor_actual = nuevo_factor
        self.size = self.base_size * self.factor_actual
        self.circle.size = (self.size, self.size)
        
        # Reposicionar usando el centro guardado
        r = self.size / 2
        self.circle.pos = (centro_x - r, centro_y - r)
        self.actualizar_borde()

    def update_color(self, dt):
        if self.rainbow:
            self.hue = (self.hue + dt * 0.15) % 1
            self.color.hsv = (self.hue, 0.6, 1)
        else:
            self.color.rgb = self.base_color

    def move(self, dt, speed):
        x, y = self.circle.pos
        x += self.vx * dt * speed
        y += self.vy * dt * speed

        # Rebotes con corrección para no quedar atrapado en los bordes
        if x <= 0:
            x = 0
            self.vx = abs(self.vx)
        elif x + self.size >= self.parent.width:
            x = self.parent.width - self.size
            self.vx = -abs(self.vx)

        if y <= BARRA_ALTURA:
            y = BARRA_ALTURA
            self.vy = abs(self.vy)
        elif y + self.size >= self.parent.height:
            y = self.parent.height - self.size
            self.vy = -abs(self.vy)

        self.circle.pos = (x, y)
        self.actualizar_borde()


# =========================
# JUEGO
# =========================
class Juego(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bolas = []
        self.paused = False
        self.speed_scale = 1
        self.evento_timer = 0

        # ======= ESTADÍSTICAS =======
        self.total_bolas = 0
        self.total_rainbow = 0
        self.total_eventos = 0
        self.tiempo = 0

        self.bg_hue = 0
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self._resize, pos=self._resize)
        self._crear_ui()

        self.lbl_evento = Label(
            text="", color=(0, 0, 0, 1), font_size=24,
            size_hint=(None, None), size=(300, 50),
            pos_hint={"center_x": 0.5, "top": 0.95}
        )
        self.add_widget(self.lbl_evento)

        Clock.schedule_interval(self.update, 1 / 60)

    def _resize(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.stats_bg.pos = (self.width * 0.1, self.height * 0.15)
        self.stats_bg.size = (self.width * 0.8, self.height * 0.7)

    def _crear_ui(self):
        with self.canvas:
            Color(0.95, 0.95, 0.95, 1)
            self.barra = Rectangle(pos=(0, 0), size=(self.width, BARRA_ALTURA))

        # Botones Inferiores
        self.btn_evento = Button(text="Evento", size_hint=(.25, None), height=BARRA_ALTURA, pos_hint={"x": 0, "y": 0})
        self.btn_evento.bind(on_release=self.evento)
        self.add_widget(self.btn_evento)

        self.btn_pausa = Button(text="Pausa", size_hint=(.25, None), height=BARRA_ALTURA, pos_hint={"x": .25, "y": 0})
        self.btn_pausa.bind(on_release=self.toggle_pausa)
        self.add_widget(self.btn_pausa)

        self.btn_reset = Button(text="Reset", size_hint=(.25, None), height=BARRA_ALTURA, pos_hint={"x": .5, "y": 0})
        self.btn_reset.bind(on_release=self.reset)
        self.add_widget(self.btn_reset)

        self.lbl = Label(text="Bolas: 0", color=(0, 0, 0, 1), size_hint=(.25, None), height=BARRA_ALTURA, pos_hint={"x": .75, "y": 0})
        self.add_widget(self.lbl)

        # Botón Stats
        self.btn_stats = Button(text="📊", size_hint=(None, None), size=(50, 50), pos_hint={"x": 0.01, "top": 0.99})
        self.btn_stats.bind(on_release=self.mostrar_stats)
        self.add_widget(self.btn_stats)

        # Panel de Stats
        self.stats_panel = FloatLayout(opacity=0)
        with self.stats_panel.canvas.before:
            Color(1, 1, 1, .95)
            self.stats_bg = Rectangle()

        self.stats_label = Label(
            text="", color=(0, 0, 0, 1), halign="left", valign="top",
            size_hint=(.7, .6), pos_hint={"center_x": .5, "center_y": .5}
        )
        self.stats_label.bind(size=self.stats_label.setter("text_size"))
        self.stats_panel.add_widget(self.stats_label)

        btn_cerrar = Button(text="Cerrar", size_hint=(None, None), size=(140, 45), pos_hint={"center_x": .5, "y": .18})
            
        btn_cerrar.bind(on_release=self.ocultar_stats)
        self.stats_panel.add_widget(btn_cerrar)
        self.add_widget(self.stats_panel)

    def ocultar_bolas(self):
        for b in self.bolas:
            b.color.a = 0
            b.border_color.a = 0

    def mostrar_bolas(self):
        for b in self.bolas:
            b.color.a = 1
            b.border_color.a = 1

    def mostrar_stats(self, *_):
        self.paused = True
        self.actualizar_stats()
        self.ocultar_bolas()
        self.stats_panel.opacity = 1

    def ocultar_stats(self, *_):
        self.stats_panel.opacity = 0
        self.mostrar_bolas()
        self.paused = False

    def actualizar_stats(self):
        m, s = divmod(int(self.tiempo), 60)
        self.stats_label.text = (
            "ESTADÍSTICAS\n\n"
            f"Bolas colocadas: {self.total_bolas}\n"
            f"Bolas rainbow: {self.total_rainbow}\n"
            f"Eventos sucedidos: {self.total_eventos}\n"
            f"Tiempo en juego: {m:02d}:{s:02d}"
        )

    def evento(self, *_):
        eventos = ["SPEED", "SLOWED", "RAINBOW", "GIANT", "MINI"]
        elegido = choice(eventos)
        self.evento_timer = EVENTO_DURACION
        self.total_eventos += 1
        self.lbl_evento.text = f"Evento: {elegido}"

        self.speed_scale = 1 # Reset de velocidad por defecto
        
        if elegido == "SPEED": self.speed_scale = 4
        elif elegido == "SLOWED": self.speed_scale = 0.35
        
        for b in self.bolas:
            if elegido == "RAINBOW": b.rainbow = True
            elif elegido == "GIANT": b.set_scale(2.0)
            elif elegido == "MINI": b.set_scale(MINI_SCALE)
            else: b.set_scale(1.0) # Si el evento no es de tamaño, reseteamos a normal

    def toggle_pausa(self, *_):
        self.paused = not self.paused
        self.btn_pausa.text = "Reanudar" if self.paused else "Pausa"

    def reset(self, *_):
        for b in self.bolas:
            self.canvas.remove(b.circle)
            self.canvas.remove(b.border)
        self.bolas.clear()
        self.lbl.text = "Bolas: 0"
        self.lbl_evento.text = ""
        self.evento_timer = 0

    def crear_bola(self, x, y):
        # Evitar crear bolas sobre la barra
        if y <= BARRA_ALTURA: return
        
        rainbow = random() < 0.25 or "RAINBOW" in self.lbl_evento.text
        giant = "GIANT" in self.lbl_evento.text
        mini = "MINI" in self.lbl_evento.text

        bola = Bola(self, x, y, rainbow, giant, mini)
        self.bolas.append(bola)
        self.total_bolas += 1
        if rainbow: self.total_rainbow += 1
        self.lbl.text = f"Bolas: {len(self.bolas)}"

    def on_touch_down(self, touch):
        if super().on_touch_down(touch): return True
        if not self.paused: self.crear_bola(touch.x, touch.y)
        return False

    def on_touch_move(self, touch):
        if not self.paused: self.crear_bola(touch.x, touch.y)
        return False

    def update(self, dt):
        self.bg_hue = (self.bg_hue + dt * 0.02) % 1
        self.bg_color.hsv = (self.bg_hue, 0.15, 1)

        if self.paused or self.stats_panel.opacity == 1: return

        self.tiempo += dt

        if self.evento_timer > 0:
            self.evento_timer -= dt
            if self.evento_timer <= 0:
                # FIN DEL EVENTO
                self.speed_scale = 1
                for b in self.bolas:
                    b.rainbow = False
                    b.set_scale(1.0) # Vuelve al tamaño original
                    b.color.rgb = b.base_color
                self.lbl_evento.text = ""

        for b in self.bolas:
            b.move(dt, self.speed_scale)
            b.update_color(dt)

class JuegoApp(App):
    def build(self): return Juego()

if __name__ == "__main__":
    JuegoApp().run()
