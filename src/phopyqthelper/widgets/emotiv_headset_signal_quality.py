import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF

class EpocXWidget(QWidget):
    """
    A reusable PyQt6 Widget that visualizes the Emotiv EPOC X electrode layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        
        # Relative positions (x, y) where (0,0) is top-left and (1,1) is bottom-right
        # Mapped according to the standard 10-20 layout and the provided visual reference.
        self.electrodes = {
            'AF3': (0.35, 0.15),
            'AF4': (0.65, 0.15),
            'F7':  (0.18, 0.25),
            'F8':  (0.82, 0.25),
            'F3':  (0.35, 0.35),
            'F4':  (0.65, 0.35),
            'FC5': (0.24, 0.45),
            'FC6': (0.76, 0.45),
            'T7':  (0.15, 0.55),
            'T8':  (0.85, 0.55),
            'RefL':(0.18, 0.68), # Left reference (CMS/DRL area)
            'RefR':(0.82, 0.68), # Right reference (CMS/DRL area)
            'P7':  (0.28, 0.80),
            'P8':  (0.72, 0.80),
            'O1':  (0.40, 0.90),
            'O2':  (0.60, 0.90),
        }

        # Emotiv quality color palette
        self.colors = {
            'grey': QColor(105, 105, 105),       # Disconnected / Unknown
            'red': QColor(220, 20, 60),          # Very Poor
            'orange': QColor(255, 140, 0),       # Poor
            'light_green': QColor(144, 238, 144),# Fair
            'dark_green': QColor(34, 139, 34),   # Good
            'black': QColor(0, 0, 0)
        }

        # Initialize all electrodes to grey
        self.electrode_states = {name: self.colors['grey'] for name in self.electrodes}
        self.electrode_states['RefL'] = self.colors['dark_green']
        self.electrode_states['RefR'] = self.colors['dark_green']

        # The plastic structural connections holding the electrodes
        self.connections = [
            ('F7', 'FC5'), ('FC5', 'T7'), ('T7', 'RefL'), ('RefL', 'P7'), ('P7', 'O1'),
            ('AF3', 'F3'),
            ('F8', 'FC6'), ('FC6', 'T8'), ('T8', 'RefR'), ('RefR', 'P8'), ('P8', 'O2'),
            ('AF4', 'F4')
        ]

    def set_electrode_color(self, name: str, color_name: str):
        """ Update the color state of a specific electrode """
        if name in self.electrode_states and color_name in self.colors:
            self.electrode_states[name] = self.colors[color_name]
            self.update() # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate responsive canvas size ensuring aspect ratio remains 1:1
        size = min(self.width(), self.height())
        offset_x = (self.width() - size) / 2
        offset_y = (self.height() - size) / 2
        
        # Scaling margins so electrodes don't clip the edge
        margin = size * 0.1
        draw_size = size - (margin * 2)

        # Helper to convert relative 0-1 coordinates to absolute canvas coordinates
        def get_abs_point(rel_pos):
            x = offset_x + margin + (rel_pos[0] * draw_size)
            y = offset_y + margin + (rel_pos[1] * draw_size)
            return QPointF(x, y)

        # 1. Draw stylized head
        center_x = self.width() / 2
        center_y = self.height() / 2
        head_radius_x = draw_size * 0.45
        head_radius_y = draw_size * 0.55
        
        head_path = QPainterPath()
        head_path.addEllipse(QPointF(center_x, center_y), head_radius_x, head_radius_y)
        
        # Add a tiny nose to indicate front facing direction
        nose_width = head_radius_x * 0.15
        nose_height = head_radius_y * 0.12
        head_path.moveTo(center_x - nose_width, center_y - head_radius_y + 10)
        head_path.lineTo(center_x, center_y - head_radius_y - nose_height)
        head_path.lineTo(center_x + nose_width, center_y - head_radius_y + 10)

        # Gradient for a soft 3D-like head appearance matching Emotiv UI roughly
        painter.setPen(QPen(QColor(200, 215, 230, 150), 3))
        painter.setBrush(QBrush(QColor(240, 245, 250))) 
        painter.drawPath(head_path)

        # 2. Draw headset structure (wires/arms)
        painter.setPen(QPen(QColor(50, 50, 50, 200), max(2, size * 0.005)))
        for start_node, end_node in self.connections:
            p1 = get_abs_point(self.electrodes[start_node])
            p2 = get_abs_point(self.electrodes[end_node])
            
            # Draw slight curve for wires
            path = QPainterPath()
            path.moveTo(p1)
            # Control point slightly bowed outward
            ctrl_x = (p1.x() + p2.x()) / 2
            if p1.x() < center_x:
                ctrl_x -= draw_size * 0.05
            else:
                ctrl_x += draw_size * 0.05
            ctrl_y = (p1.y() + p2.y()) / 2
            
            path.quadTo(QPointF(ctrl_x, ctrl_y), p2)
            painter.drawPath(path)

        # 3. Draw Electrodes
        electrode_radius = draw_size * 0.04
        font_size = max(6, int(electrode_radius * 0.65))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)

        for name, pos in self.electrodes.items():
            pt = get_abs_point(pos)
            color = self.electrode_states[name]

            if name in ['RefL', 'RefR']:
                # References have special UI: black outer ring, colored inner circle
                painter.setPen(QPen(QColor(0, 0, 0), max(2, size * 0.01)))
                painter.setBrush(QBrush(QColor(0, 0, 0)))
                painter.drawEllipse(pt, electrode_radius, electrode_radius)
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius * 0.4, electrode_radius * 0.4)
            else:
                # Standard Electrodes
                painter.setPen(QPen(QColor(20, 20, 20), max(1, size * 0.003)))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius, electrode_radius)

                # Draw text label in the center
                # White text for dark/red colors, black for lighter ones for contrast
                if color in [self.colors['grey'], self.colors['light_green']]:
                    painter.setPen(QColor(0, 0, 0))
                else:
                    painter.setPen(QColor(255, 255, 255))
                
                # Center text inside the circle
                text_rect = QRectF(pt.x() - electrode_radius, pt.y() - electrode_radius, 
                                   electrode_radius * 2, electrode_radius * 2)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, name)


# Example usage block to demonstrate integration
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Setup Main Window
    window = QWidget()
    window.setWindowTitle("Emotiv EPOC X Layout Widget")
    layout = QVBoxLayout()
    
    # Initialize our custom widget
    headset_widget = EpocXWidget()
    
    # Set the state to match the user's uploaded screenshot perfectly
    screenshot_state = {
        'F7': 'red', 'AF3': 'red', 'F3': 'red', 'T7': 'red', 'P7': 'red',
        'FC5': 'grey', 'F4': 'grey', 'O1': 'grey',
        'AF4': 'dark_green', 'F8': 'dark_green', 'FC6': 'dark_green',
        'T8': 'light_green', 'P8': 'light_green', 'O2': 'light_green'
    }
    
    for electrode, state in screenshot_state.items():
        headset_widget.set_electrode_color(electrode, state)

    layout.addWidget(headset_widget)
    window.setLayout(layout)
    window.resize(600, 600)
    window.show()
    
    sys.exit(app.exec())
