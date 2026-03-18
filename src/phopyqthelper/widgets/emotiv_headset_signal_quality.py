import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QRadialGradient
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


# ==================================================================================================================================================================================================================================================================================== #
# Left-Only Headset View                                                                                                                                                                                                                                                               #
# ==================================================================================================================================================================================================================================================================================== #

class LeftOnlyHeadsetQualityWidget(QWidget):
    """
    A reusable PyQt6 Widget that visualizes the left profile of the Emotiv EPOC X.
    Displays left-hemisphere electrodes and central/reference sensors.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        
        # Relative positions (x, y) where (0,0) is top-left and (1,1) is bottom-right
        # Mapped to match the specific 2D side-profile view from the Emotiv software.
        self.electrodes = {
            'F7':  (0.15, 0.32),
            'AF3': (0.25, 0.22),
            'F3':  (0.35, 0.30),
            'FC5': (0.22, 0.42),
            'T7':  (0.55, 0.25),
            'O1':  (0.70, 0.36),
            'P7':  (0.82, 0.30),
            'RefL':(0.65, 0.55), # Left Reference
        }

        # Connection anchor points on the main black structural band
        self.anchors = {
            'F7':  (0.28, 0.43),
            'AF3': (0.32, 0.42),
            'F3':  (0.40, 0.41),
            'FC5': (0.25, 0.44),
            'T7':  (0.52, 0.40),
            'O1':  (0.75, 0.42),
            'P7':  (0.80, 0.43),
            'RefL':(0.65, 0.42),
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

        # Initialize all to grey by default
        self.electrode_states = {name: self.colors['grey'] for name in self.electrodes}
        self.electrode_states['RefL'] = self.colors['dark_green']

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
        
        # Scaling margins
        margin = size * 0.1
        draw_size = size - (margin * 2)

        # Helper to convert relative 0-1 coordinates to absolute canvas coordinates
        def get_abs_point(rel_pos):
            x = offset_x + margin + (rel_pos[0] * draw_size)
            y = offset_y + margin + (rel_pos[1] * draw_size)
            return QPointF(x, y)

        # 1. Draw Stylized Side-Profile Head (Facing Left)
        head_path = QPainterPath()
        head_path.moveTo(get_abs_point((0.5, 0.1))) # Top of head
        head_path.cubicTo(get_abs_point((0.8, 0.1)), get_abs_point((0.95, 0.3)), get_abs_point((0.9, 0.5))) # Back curve
        head_path.quadTo(get_abs_point((0.8, 0.7)), get_abs_point((0.75, 0.95))) # Back of neck
        head_path.lineTo(get_abs_point((0.45, 0.95))) # Base of neck
        head_path.quadTo(get_abs_point((0.4, 0.8)), get_abs_point((0.2, 0.75))) # Front of neck/jaw
        head_path.quadTo(get_abs_point((0.15, 0.7)), get_abs_point((0.18, 0.65))) # Chin/Mouth
        head_path.quadTo(get_abs_point((0.15, 0.6)), get_abs_point((0.08, 0.55))) # Nose
        head_path.quadTo(get_abs_point((0.05, 0.45)), get_abs_point((0.15, 0.4))) # Bridge of nose
        head_path.quadTo(get_abs_point((0.18, 0.3)), get_abs_point((0.25, 0.2))) # Forehead
        head_path.quadTo(get_abs_point((0.35, 0.1)), get_abs_point((0.5, 0.1))) # Back to top

        # Blue 3D-like gradient for the head mimicking the software UI
        center_pt = get_abs_point((0.5, 0.5))
        gradient = QRadialGradient(center_pt.x(), center_pt.y(), size * 0.6)
        gradient.setColorAt(0.0, QColor(130, 180, 255, 230))  # Light blue core
        gradient.setColorAt(1.0, QColor(50, 100, 210, 160))   # Darker blue edges
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(head_path)

        # 2. Draw Connecting Arms (Under the band)
        painter.setPen(QPen(QColor(25, 25, 25), max(4, size * 0.015), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for name, pos in self.electrodes.items():
            anchor = get_abs_point(self.anchors[name])
            pt = get_abs_point(pos)
            painter.drawLine(anchor, pt)

        # 3. Draw Thick Main Band
        band_path = QPainterPath()
        band_path.moveTo(get_abs_point((0.20, 0.44))) # Front edge
        # Slight curve sagging in the middle conforming to the head
        band_path.quadTo(get_abs_point((0.55, 0.38)), get_abs_point((0.90, 0.44))) 
        painter.setPen(QPen(QColor(20, 20, 20), max(12, size * 0.07), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(band_path)

        # 4. Draw Faint 'EPOC X' Logo on the band
        painter.save()
        logo_pt = get_abs_point((0.35, 0.43))
        painter.translate(logo_pt)
        painter.rotate(-4) # Slight upward angle to match the band's curve
        painter.setPen(QColor(60, 60, 60)) # Faint grey
        painter.setFont(QFont("Arial", max(6, int(size * 0.018)), QFont.Weight.Bold))
        painter.drawText(QRectF(0, -10, 100, 20), Qt.AlignmentFlag.AlignLeft, "EPOC X")
        painter.restore()

        # 5. Draw Electrodes & Labels
        electrode_radius = draw_size * 0.045
        font_size = max(6, int(electrode_radius * 0.6))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)

        for name, pos in self.electrodes.items():
            pt = get_abs_point(pos)
            color = self.electrode_states[name]

            if name == 'RefL':
                # Reference sensor unique UI: thick colored border, black middle, colored dot
                painter.setPen(QPen(color, max(2, electrode_radius * 0.35)))
                painter.setBrush(QBrush(QColor(20, 20, 20)))
                painter.drawEllipse(pt, electrode_radius * 0.9, electrode_radius * 0.9)
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius * 0.35, electrode_radius * 0.35)
            else:
                # Standard Electrodes: Black border, colored background
                painter.setPen(QPen(QColor(20, 20, 20), max(1, size * 0.003)))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius, electrode_radius)

                # Draw text label in the center
                if color in [self.colors['grey'], self.colors['light_green']]:
                    painter.setPen(QColor(0, 0, 0)) # Dark text for light backgrounds
                else:
                    painter.setPen(QColor(255, 255, 255)) # Light text for dark backgrounds
                
                text_rect = QRectF(pt.x() - electrode_radius, pt.y() - electrode_radius, 
                                   electrode_radius * 2, electrode_radius * 2)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, name)


# ==================================================================================================================================================================================================================================================================================== #
# Right-Only Headset View                                                                                                                                                                                                                                                              #
# ==================================================================================================================================================================================================================================================================================== #
class RightOnlyHeadsetQualityWidget(QWidget):
    """
    A reusable PyQt6 Widget that visualizes the right profile of the Emotiv EPOC X.
    Displays right-hemisphere electrodes and central/reference sensors.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        
        # Relative positions (x, y) mapped to the right-facing 2D side-profile view.
        self.electrodes = {
            'F8':  (0.85, 0.32),
            'AF4': (0.75, 0.22),
            'F4':  (0.65, 0.30),
            'FC6': (0.78, 0.42),
            'T8':  (0.45, 0.25),
            'O2':  (0.30, 0.36),
            'P8':  (0.18, 0.30),
            'RefR':(0.35, 0.55), # Right Reference
        }

        # Connection anchor points on the main black structural band
        self.anchors = {
            'F8':  (0.72, 0.43),
            'AF4': (0.68, 0.42),
            'F4':  (0.60, 0.41),
            'FC6': (0.75, 0.44),
            'T8':  (0.48, 0.40),
            'O2':  (0.25, 0.42),
            'P8':  (0.20, 0.43),
            'RefR':(0.35, 0.42),
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

        # Initialize all to grey by default
        self.electrode_states = {name: self.colors['grey'] for name in self.electrodes}
        self.electrode_states['RefR'] = self.colors['dark_green']

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
        
        # Scaling margins
        margin = size * 0.1
        draw_size = size - (margin * 2)

        # Helper to convert relative 0-1 coordinates to absolute canvas coordinates
        def get_abs_point(rel_pos):
            x = offset_x + margin + (rel_pos[0] * draw_size)
            y = offset_y + margin + (rel_pos[1] * draw_size)
            return QPointF(x, y)

        # 1. Draw Stylized Side-Profile Head (Facing Right)
        # This is a mathematically mirrored version of the left-facing head path
        head_path = QPainterPath()
        head_path.moveTo(get_abs_point((0.5, 0.1))) # Top of head
        head_path.cubicTo(get_abs_point((0.2, 0.1)), get_abs_point((0.05, 0.3)), get_abs_point((0.1, 0.5))) # Back curve
        head_path.quadTo(get_abs_point((0.2, 0.7)), get_abs_point((0.25, 0.95))) # Back of neck
        head_path.lineTo(get_abs_point((0.55, 0.95))) # Base of neck
        head_path.quadTo(get_abs_point((0.6, 0.8)), get_abs_point((0.8, 0.75))) # Front of neck/jaw
        head_path.quadTo(get_abs_point((0.85, 0.7)), get_abs_point((0.82, 0.65))) # Chin/Mouth
        head_path.quadTo(get_abs_point((0.85, 0.6)), get_abs_point((0.92, 0.55))) # Nose
        head_path.quadTo(get_abs_point((0.95, 0.45)), get_abs_point((0.85, 0.4))) # Bridge of nose
        head_path.quadTo(get_abs_point((0.82, 0.3)), get_abs_point((0.75, 0.2))) # Forehead
        head_path.quadTo(get_abs_point((0.65, 0.1)), get_abs_point((0.5, 0.1))) # Back to top

        # Blue 3D-like gradient for the head mimicking the software UI
        center_pt = get_abs_point((0.5, 0.5))
        gradient = QRadialGradient(center_pt.x(), center_pt.y(), size * 0.6)
        gradient.setColorAt(0.0, QColor(130, 180, 255, 230))  # Light blue core
        gradient.setColorAt(1.0, QColor(50, 100, 210, 160))   # Darker blue edges
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(head_path)

        # 2. Draw Connecting Arms (Under the band)
        painter.setPen(QPen(QColor(25, 25, 25), max(4, size * 0.015), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for name, pos in self.electrodes.items():
            anchor = get_abs_point(self.anchors[name])
            pt = get_abs_point(pos)
            painter.drawLine(anchor, pt)

        # 3. Draw Thick Main Band (Mirrored)
        band_path = QPainterPath()
        band_path.moveTo(get_abs_point((0.80, 0.44))) # Front edge
        # Slight curve sagging in the middle conforming to the head
        band_path.quadTo(get_abs_point((0.45, 0.38)), get_abs_point((0.10, 0.44))) 
        painter.setPen(QPen(QColor(20, 20, 20), max(12, size * 0.07), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawPath(band_path)

        # 4. Draw Faint 'EPOC X' Logo on the band (Mirrored for right side view)
        painter.save()
        logo_pt = get_abs_point((0.65, 0.43))
        painter.translate(logo_pt)
        painter.rotate(4) # Slight upward angle to match the band's curve
        painter.scale(-1, 1) # Flip horizontally so it appears backwards like the Emotiv UI snapshot
        painter.setPen(QColor(60, 60, 60)) # Faint grey
        painter.setFont(QFont("Arial", max(6, int(size * 0.018)), QFont.Weight.Bold))
        # Draw mirrored text relative to the flipped coordinate system
        painter.drawText(QRectF(0, -10, 100, 20), Qt.AlignmentFlag.AlignLeft, "EPOC X")
        painter.restore()

        # 5. Draw Electrodes & Labels
        electrode_radius = draw_size * 0.045
        font_size = max(6, int(electrode_radius * 0.6))
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)

        for name, pos in self.electrodes.items():
            pt = get_abs_point(pos)
            color = self.electrode_states[name]

            if name == 'RefR':
                # Reference sensor unique UI: thick colored border, black middle, colored dot
                painter.setPen(QPen(color, max(2, electrode_radius * 0.35)))
                painter.setBrush(QBrush(QColor(20, 20, 20)))
                painter.drawEllipse(pt, electrode_radius * 0.9, electrode_radius * 0.9)
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius * 0.35, electrode_radius * 0.35)
            else:
                # Standard Electrodes: Black border, colored background
                painter.setPen(QPen(QColor(20, 20, 20), max(1, size * 0.003)))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(pt, electrode_radius, electrode_radius)

                # Draw text label in the center
                if color in [self.colors['grey'], self.colors['light_green']]:
                    painter.setPen(QColor(0, 0, 0)) # Dark text for light backgrounds
                else:
                    painter.setPen(QColor(255, 255, 255)) # Light text for dark backgrounds
                
                text_rect = QRectF(pt.x() - electrode_radius, pt.y() - electrode_radius, 
                                   electrode_radius * 2, electrode_radius * 2)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, name)




# ==================================================================================================================================================================================================================================================================================== #
# Testing Code                                                                                                                                                                                                                                                                         #
# ==================================================================================================================================================================================================================================================================================== #

# Example usage block to demonstrate integration
def test_right_only_headset(): 
    
    # Setup Main Window
    window = QWidget()
    window.setWindowTitle("Emotiv EPOC X - Right Profile Widget")
    window.setStyleSheet("background-color: white;") # Ensures contrast for the blue head
    layout = QVBoxLayout()
    
    # Initialize our custom widget
    headset_widget = RightOnlyHeadsetQualityWidget()
    
    # Set the state to match the user's uploaded right-profile screenshot perfectly
    screenshot_state = {
        'AF4': 'red', 
        'F8': 'grey', 
        'F4': 'dark_green', 
        'FC6': 'dark_green', 
        'T8': 'dark_green', 
        'P8': 'dark_green',
        'O2': 'dark_green',
        'RefR': 'dark_green'
    }
    
    for electrode, state in screenshot_state.items():
        headset_widget.set_electrode_color(electrode, state)

    layout.addWidget(headset_widget)
    window.setLayout(layout)
    window.resize(600, 600)
    window.show()
    
    return window, layout, headset_widget





# Example usage block to demonstrate integration
def test_left_only_headset():    
    # Setup Main Window
    window = QWidget()
    window.setWindowTitle("Emotiv EPOC X - Left Profile Widget")
    window.setStyleSheet("background-color: white;") # Ensures contrast for the blue head
    layout = QVBoxLayout()
    
    # Initialize our custom widget
    headset_widget = LeftOnlyHeadsetQualityWidget()
    
    # Set the state to match the user's uploaded side-profile screenshot perfectly
    screenshot_state = {
        'F7': 'dark_green', 
        'AF3': 'dark_green', 
        'F3': 'dark_green', 
        'FC5': 'grey', 
        'T7': 'dark_green', 
        'P7': 'grey',
        'O1': 'dark_green',
        'RefL': 'dark_green'
    }
    
    for electrode, state in screenshot_state.items():
        headset_widget.set_electrode_color(electrode, state)

    layout.addWidget(headset_widget)
    window.setLayout(layout)
    window.resize(600, 600)
    window.show()
    
    return window, layout, headset_widget




def test_overhead_full_headset():    
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
    
    return window, layout, headset_widget









# Example usage block to demonstrate integration
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    _overhead_out = test_overhead_full_headset()
    _left_out = test_left_only_headset()
    _right_out = test_right_only_headset()

    sys.exit(app.exec())
