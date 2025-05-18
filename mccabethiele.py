import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGroupBox, QDoubleSpinBox, QMessageBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class McCabeThieleCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("McCabe-Thiele Method Calculator")
        self.setGeometry(100, 100, 1000, 700)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.create_ui()

    def create_ui(self):
        main_layout = QHBoxLayout(self.main_widget)

        # Left panel for inputs
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignTop)

        input_group = QGroupBox("Input Parameters")
        input_layout = QVBoxLayout()

        # Input fields
        self.inputs = {}
        for label, min_val, max_val, step, default in [
            ("xF", 0.0, 1.0, 0.01, 0.5),
            ("xD", 0.0, 1.0, 0.01, 0.9),
            ("xW", 0.0, 1.0, 0.01, 0.1),
            ("q", 0.0, 500.0, 0.01, 1.0),
            ("R", 0.0, 500.0, 0.1, 2.0),
            ("alpha", 0.0, 10.0, 0.1, 2.5)
        ]:
            box = self.create_spinbox_input(label, min_val, max_val, step, default)
            self.inputs[label] = box.findChild(QDoubleSpinBox)
            input_layout.addWidget(box)

        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)

        self.calculate_btn = QPushButton("Calculate Stages")
        self.calculate_btn.clicked.connect(self.calculate)
        left_layout.addWidget(self.calculate_btn)

        self.results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.stages_label = QLabel("Theoretical stages: ")
        self.feed_stage_label = QLabel("Feed stage: ")
        results_layout.addWidget(self.stages_label)
        results_layout.addWidget(self.feed_stage_label)
        self.results_group.setLayout(results_layout)
        left_layout.addWidget(self.results_group)

        self.plot_widget = QWidget()
        plot_layout = QVBoxLayout(self.plot_widget)
        self.figure = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        plot_layout.addWidget(self.canvas)

        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(self.plot_widget, stretch=2)

    def create_spinbox_input(self, label, min_val, max_val, step, default_val):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(f"{label}:")
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setValue(default_val)
        spinbox.setDecimals(3)

        layout.addWidget(lbl, stretch=2)
        layout.addWidget(spinbox, stretch=1)

        return widget

    def calculate(self):
        try:
            xF = self.inputs['xF'].value()
            xD = self.inputs['xD'].value()
            xW = self.inputs['xW'].value()
            q = self.inputs['q'].value()
            R = self.inputs['R'].value()
            alpha = self.inputs['alpha'].value()

            if not (xD > xF > xW):
                QMessageBox.warning(self, "Input Error", "Compositions must satisfy: xD > xF > xW")
                return

            stages, feed_stage = self.perform_mccabe_thiele(xF, xD, xW, q, R, alpha)
            self.stages_label.setText(f"Theoretical stages: {stages}")
            self.feed_stage_label.setText(f"Feed stage: {feed_stage}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def perform_mccabe_thiele(self, xF, xD, xW, q, R, alpha):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Equilibrium curve
        x = np.linspace(0.001, 0.999, 500)
        y_eq = (alpha * x) / (1 + (alpha - 1) * x)
        ax.plot(x, y_eq, label="Equilibrium Curve", color='blue')

        # Diagonal
        ax.plot([0, 1], [0, 1], '-.', color='black', label="y = x")

        # q-line
        if q == 1:
            # For q = 1, plot a vertical line at x = xF
            x_q = np.full_like(np.linspace(0, 1, 500), xF)
            y_q = np.linspace(0, 1, 500)
            q_text = f'q-line: vertical at x = {xF:.2f}'
        else:
            # For q != 1, use the original calculation for slope and intercept
            slope_q = q / (q - 1)
            intercept_q = xF / (1 - q)
            x_q = np.linspace(0, 1, 500)
            y_q = slope_q * x_q + intercept_q
            q_text = f'q-line: y = {slope_q:.2f}x + {intercept_q:.2f}'

        ax.plot(x_q, y_q, label='q-Line', color='green')
        ax.text(0.05, 0.9, q_text, color='green', fontsize=8)


        # Enriching OL
        slope_r = R / (R + 1)
        intercept_r = xD / (R + 1)
        y_r = slope_r * x + intercept_r
        ax.plot(x, y_r, label='Enriching Section OL', color='red')
        ax.text(0.05, 0.85, f'Enriching OL: y = {slope_r:.2f}x + {intercept_r:.2f}', color='red', fontsize=8)

        # Find intersection
        x_int = (intercept_q - intercept_r) / (slope_r - slope_q) if q != 1 else xF
        y_int = slope_r * x_int + intercept_r

        # Stripping OL
        slope_s = (y_int - xW) / (x_int - xW)
        intercept_s = xW - slope_s * xW
        y_s = slope_s * x + intercept_s
        ax.plot(x, y_s, label='Stripping Section OL', color='purple')
        ax.text(0.05, 0.80, f'Stripping OL: y = {slope_s:.2f}x + {intercept_s:.2f}', color='purple', fontsize=8)

        # Stage construction
        stages = 0
        feed_stage = None
        x_curr = xD
        y_curr = xD
        is_stripping = False

        while x_curr > xW + 1e-3:
            # Horizontal to equilibrium
            x_next = y_curr / (alpha - (alpha - 1) * y_curr)
            y_prev = y_curr
            ax.plot([x_curr, x_next], [y_curr, y_curr], 'k--')
            x_curr = x_next

            # Vertical to equilibrium
            ax.plot([x_next, x_next], [y_curr, y_curr + 1e-6], 'k--')  # Vertical dotted line
    

            # Decide OL
            if not is_stripping and x_curr < x_int:
                is_stripping = True
                feed_stage = stages + 1

            if not is_stripping:
                y_curr = slope_r * x_curr + intercept_r
                ax.plot([x_curr, x_curr], [y_curr, y_prev], linestyle='--', color='black')

            else:
                y_curr = slope_s * x_curr + intercept_s
                ax.plot([x_curr, x_curr], [y_curr, y_prev], linestyle='--', color='black')


            ax.plot([x_curr, x_curr], [y_curr, y_curr + 1e-6], 'k--')
            ax.plot([x_curr, x_curr], [y_curr, y_curr], 'k--')
            ax.plot([x_curr, x_curr], [y_curr, y_curr], 'ko', markersize=2)


             # Add stage number label
            ax.text(x_curr + 0.01, y_curr, str(stages + 1), fontsize=8, ha='center', va='bottom')  # Label each stage
    
            stages += 1

        # Final decorations
        ax.plot([xF], [xF], 'bo', label='Feed')
        ax.plot([xD], [xD], 'go', label='Distillate')
        ax.plot([xW], [xW], 'mo', label='Residue')
        ax.plot([x_int], [y_int], 'ro', label='Feed Stage')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('x (liquid composition)')
        ax.set_ylabel('y (vapor composition)')
        ax.set_title('McCabe-Thiele Diagram')
        ax.grid(True)
        ax.legend(loc='best')

        self.canvas.draw()

        return stages, feed_stage


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = McCabeThieleCalculator()
    window.show()
    sys.exit(app.exec_())
