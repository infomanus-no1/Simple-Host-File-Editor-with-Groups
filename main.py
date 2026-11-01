import sys
import os
import ctypes
import platform
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QLineEdit, QLabel, QMessageBox, QHeaderView, QPlainTextEdit, QDialog,
                             QMenu) # <-- QMenu importálva
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut # <-- Gyorsbillentyűk importálva

# --- GLOBÁLIS HIBAKEZELŐ ---
def global_exception_handler(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Végzetes Hiba")
    msg_box.setText("A program váratlan hibába ütközött:")
    msg_box.setDetailedText(error_msg)
    msg_box.exec()

sys.excepthook = global_exception_handler

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    if not is_admin():
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"

# --- PROFI, MAGAS KONTRASZTÚ TÉMÁK ---
DARK_THEME = """
    QMainWindow, QDialog, QMessageBox, QMenu { background-color: #121212; color: #FFFFFF; }
    QWidget { color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    QTreeWidget { background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #333333; border-radius: 6px; alternate-background-color: #252525; }
    QTreeWidget::item { color: #E0E0E0; padding: 4px; }
    QTreeWidget::item:hover { background-color: #2D2D2D; }
    QTreeWidget::item:selected { background-color: #BB86FC; color: #000000; }
    QHeaderView::section { background-color: #2D2D2D; color: #BB86FC; padding: 6px; font-weight: bold; border: 1px solid #333333; }
    QPushButton { background-color: #BB86FC; color: #121212; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; }
    QPushButton:hover { background-color: #D7B4FE; }
    QPushButton:pressed { background-color: #3700B3; color: #FFFFFF; }
    QLineEdit, QPlainTextEdit { background-color: #1E1E1E; border: 1px solid #BB86FC; border-radius: 5px; padding: 6px; color: #FFFFFF; selection-background-color: #BB86FC; selection-color: #121212; }
    QLabel { color: #FFFFFF; }
    QMenu::item:selected { background-color: #BB86FC; color: #000000; }
"""

LIGHT_THEME = """
    QMainWindow, QDialog, QMessageBox, QMenu { background-color: #F8F9FA; color: #212529; }
    QWidget { color: #212529; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    QTreeWidget { background-color: #FFFFFF; color: #212529; border: 1px solid #CED4DA; border-radius: 6px; alternate-background-color: #F1F3F5; }
    QTreeWidget::item { color: #212529; padding: 4px; }
    QTreeWidget::item:hover { background-color: #E9ECEF; }
    QTreeWidget::item:selected { background-color: #6200EE; color: #FFFFFF; }
    QHeaderView::section { background-color: #E9ECEF; color: #6200EE; padding: 6px; font-weight: bold; border: 1px solid #CED4DA; }
    QPushButton { background-color: #6200EE; color: #FFFFFF; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; }
    QPushButton:hover { background-color: #4B00D1; }
    QPushButton:pressed { background-color: #3700B3; }
    QLineEdit, QPlainTextEdit { background-color: #FFFFFF; border: 1px solid #6200EE; border-radius: 5px; padding: 6px; color: #212529; selection-background-color: #6200EE; selection-color: #FFFFFF; }
    QLabel { color: #212529; }
    QMenu::item:selected { background-color: #6200EE; color: #FFFFFF; }
"""

def get_base_domain(domain):
    parts = domain.split('.')
    if len(parts) > 2:
        return '.'.join(parts[-2:])
    return domain

class HostsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Modern Hosts Szerkesztő (Intelligens Csoportosítás)")
        self.resize(900, 700)
        self.is_dark = True
        self.old_item_text = ""
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.apply_theme()
        self.load_hosts()

    def setup_ui(self):
        top_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP Cím (pl. 127.0.0.1)")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Domain (pl. localhost)")
        
        add_btn = QPushButton("Hozzáadás")
        add_btn.clicked.connect(self.add_single_entry)
        bulk_btn = QPushButton("Tömeges Hozzáadás")
        bulk_btn.clicked.connect(self.open_bulk_dialog)
        theme_btn = QPushButton("🌓 Téma Váltás")
        theme_btn.clicked.connect(self.toggle_theme)

        top_layout.addWidget(self.ip_input)
        top_layout.addWidget(self.host_input)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(bulk_btn)
        top_layout.addWidget(theme_btn)
        self.layout.addLayout(top_layout)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Kategória (Megjegyzés) ➔ IP Cím ➔ Domain"])
        
        # --- ÚJ: Többes kijelölés engedélyezése ---
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        
        # --- ÚJ: Jobb klikkes menü engedélyezése ---
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        self.layout.addWidget(self.tree)

        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.itemChanged.connect(self.on_item_changed)

        bottom_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Mentés a hosts fájlba")
        save_btn.clicked.connect(self.save_hosts)
        bottom_layout.addWidget(save_btn)
        self.layout.addLayout(bottom_layout)

        # --- ÚJ: Gyorsbillentyűk beállítása ---
        QShortcut(QKeySequence("Delete"), self.tree, self.delete_selected)
        QShortcut(QKeySequence("Ctrl+C"), self.tree, self.copy_selected)

    # --- ÚJ: Jobb klikkes menü ---
    def show_context_menu(self, position):
        if not self.tree.selectedItems():
            return
            
        menu = QMenu()
        copy_action = menu.addAction("📋 Másolás (Ctrl+C)")
        delete_action = menu.addAction("🗑️ Törlés (Del)")
        
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if action == copy_action:
            self.copy_selected()
        elif action == delete_action:
            self.delete_selected()

    # --- ÚJ: Kijelöltek másolása vágólapra ---
    def copy_selected(self):
        items = self.tree.selectedItems()
        if not items: return
        
        text_lines = [item.text(0) for item in items]
        QApplication.clipboard().setText("\n".join(text_lines))

    # --- ÚJ: Kijelöltek törlése (Intelligens takarítással) ---
    def delete_selected(self):
        items = self.tree.selectedItems()
        if not items: return

        # Válasz a biztonságos törlésre: A PyQt6-ban egy szülő törlése törli a gyerekeit is.
        # Meg kell vizsgálnunk, hogy az elem még létezik-e a fában (treeWidget != None)
        for item in items:
            if item.treeWidget() is None:
                continue # Ha a szülőjét már töröltük, a gyerek is elveszett, ugrunk rajta
                
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                # Top level (Kategória)
                idx = self.tree.indexOfTopLevelItem(item)
                if idx >= 0:
                    self.tree.takeTopLevelItem(idx)

        # Üres IP-k és üres Kategóriák takarítása (visszafelé haladva)
        for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
            cat_item = self.tree.topLevelItem(i)
            for j in range(cat_item.childCount() - 1, -1, -1):
                ip_item = cat_item.child(j)
                if ip_item.childCount() == 0:
                    cat_item.removeChild(ip_item)
            if cat_item.childCount() == 0:
                self.tree.takeTopLevelItem(i)

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark else LIGHT_THEME
        QApplication.instance().setStyleSheet(theme)
        
        cat_color = QColor("#BB86FC") if self.is_dark else QColor("#6200EE")
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setForeground(0, cat_color)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()

    def load_hosts(self):
        # UI frissítés és jelek blokkolása a drasztikus gyorsítás érdekében
        self.tree.blockSignals(True)
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        
        if not os.path.exists(HOSTS_PATH):
            self.tree.blockSignals(False)
            self.tree.setUpdatesEnabled(True)
            return

        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Gyorsítótár: szótárban építjük fel a struktúrát GUI műveletek helyett
        structure = {}
        current_category = ""
        total_nodes = 0
        
        for line in lines:
            line = line.strip()
            
            if not line:
                current_category = ""
                continue
                
            # Kategória kommentek felismerése
            if line.startswith("#"):
                if "Automatikus" not in line and "===" not in line and "---" not in line:
                    current_category = line
                continue
            
            # --- JAVÍTÁS: Sorvégi inline kommentek levágása darabolás előtt ---
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                domains = parts[1:]
                
                if not current_category:
                    base = get_base_domain(domains[0])
                    category_name = f"# [Auto] {base}"
                else:
                    category_name = current_category
                
                if category_name not in structure:
                    structure[category_name] = {}
                if ip not in structure[category_name]:
                    structure[category_name][ip] = set()
                
                for d in domains:
                    structure[category_name][ip].add(d)
                    total_nodes += 1

        # GUI elemek tömeges (Batch) generálása
        top_items = []
        cat_font = QFont()
        cat_font.setBold(True)
        cat_font.setPointSize(11)
        ip_font = QFont()
        ip_font.setItalic(True)
        cat_color = QColor("#BB86FC") if self.is_dark else QColor("#6200EE")

        for cat_name, ips in structure.items():
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setFlags(cat_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cat_item.setFont(0, cat_font)
            cat_item.setForeground(0, cat_color)
            
            for ip, domains in ips.items():
                ip_item = QTreeWidgetItem([ip])
                ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
                ip_item.setFont(0, ip_font)
                cat_item.addChild(ip_item)
                
                for domain in domains:
                    domain_item = QTreeWidgetItem([domain])
                    domain_item.setFlags(domain_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    ip_item.addChild(domain_item)
                    
            top_items.append(cat_item)
            
        # Fő elemek egyszerre történő betöltése a fába
        self.tree.addTopLevelItems(top_items)
        
        # Csak akkor nyitjuk le az összes ágat automatikusan, ha nincs extrém sok elem (megelőzi a kifagyást)
        if total_nodes < 1500:
            self.tree.expandAll()
            
        self.apply_theme()
        self.tree.setUpdatesEnabled(True)
        self.tree.blockSignals(False)

    def find_item(self, parent, text):
        # A beépített C++ szintű PyQt kereső használata a Python loop helyett
        if parent == self.tree:
            items = self.tree.findItems(text, Qt.MatchFlag.MatchExactly, 0)
            return items[0] if items else None
        else:
            for i in range(parent.childCount()):
                if parent.child(i).text(0) == text:
                    return parent.child(i)
        return None

    def merge_into_tree(self, category, ip, domains):
        self.tree.blockSignals(True)
        
        cat_item = self.find_item(self.tree, category)
        if not cat_item:
            cat_item = QTreeWidgetItem([category])
            cat_item.setFlags(cat_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cat_font = cat_item.font(0)
            cat_font.setBold(True)
            cat_font.setPointSize(11)
            cat_item.setFont(0, cat_font)
            
            cat_color = QColor("#BB86FC") if self.is_dark else QColor("#6200EE")
            cat_item.setForeground(0, cat_color)
            self.tree.addTopLevelItem(cat_item)

        ip_item = self.find_item(cat_item, ip)
        if not ip_item:
            ip_item = QTreeWidgetItem([ip])
            ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
            ip_font = ip_item.font(0)
            ip_font.setItalic(True)
            ip_item.setFont(0, ip_font)
            cat_item.addChild(ip_item)

        for domain in domains:
            if not self.find_item(ip_item, domain):
                domain_item = QTreeWidgetItem([domain])
                domain_item.setFlags(domain_item.flags() | Qt.ItemFlag.ItemIsEditable)
                ip_item.addChild(domain_item)
                
        self.tree.blockSignals(False)

    def add_single_entry(self):
        ip = self.ip_input.text().strip()
        domain = self.host_input.text().strip()
        if ip and domain:
            base = get_base_domain(domain)
            self.merge_into_tree(f"# [Új] {base}", ip, [domain])
            self.ip_input.clear()
            self.host_input.clear()
            self.tree.expandAll()

    def open_bulk_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Tömeges hozzáadás")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Minden sor egy bejegyzés legyen: IP Domain (pl. 127.0.0.1 teszt.local)"))
        text_edit = QPlainTextEdit()
        btn = QPushButton("Feldolgozás")
        
        layout.addWidget(text_edit)
        layout.addWidget(btn)
        
        def process():
            self.tree.setUpdatesEnabled(False)
            for line in text_edit.toPlainText().split('\n'):
                line = line.strip()
                if "#" in line:
                    line = line.split("#", 1)[0].strip() # Inline komment szűrés itt is
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    ip, domains = parts[0], parts[1:]
                    base = get_base_domain(domains[0])
                    self.merge_into_tree(f"# [Tömeges] {base}", ip, domains)
            dialog.accept()
            self.tree.setUpdatesEnabled(True)
            self.tree.expandAll()
            
        btn.clicked.connect(process)
        dialog.exec()

    def on_item_double_clicked(self, item, column):
        self.old_item_text = item.text(0)

    def on_item_changed(self, item, column):
        new_text = item.text(0).strip()
        if not new_text:
            self.revert_edit(item, "A mező nem lehet üres!")
            return

        parent = item.parent()
        
        if not parent:
            if not new_text.startswith("#"):
                self.revert_edit(item, "A kategóriának '#' jellel kell kezdődnie (komment)!")
                return
        else:
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child != item and child.text(0) == new_text:
                    self.revert_edit(item, f"A(z) '{new_text}' már létezik ezen a szinten!")
                    return

    def revert_edit(self, item, message):
        self.tree.blockSignals(True)
        QMessageBox.warning(self, "Ütközés", message)
        item.setText(0, self.old_item_text)
        self.tree.blockSignals(False)

    def save_hosts(self):
        try:
            with open(HOSTS_PATH, "w", encoding="utf-8") as f:
                f.write("# Automatikusan generálva a Modern Hosts Editor által\n")
                f.write("# ==================================================\n\n")
                
                for i in range(self.tree.topLevelItemCount()):
                    cat_item = self.tree.topLevelItem(i)
                    f.write(f"\n{cat_item.text(0)}\n")
                    
                    for j in range(cat_item.childCount()):
                        ip_item = cat_item.child(j)
                        ip = ip_item.text(0)
                        
                        domains = []
                        for k in range(ip_item.childCount()):
                            domains.append(ip_item.child(k).text(0))
                            
                        if domains:
                            f.write(f"{ip}\t{' '.join(domains)}\n")
                            
            QMessageBox.information(self, "Siker", "A hosts fájl sikeresen frissítve!")
        except PermissionError:
            QMessageBox.critical(self, "Hiba", "Nincs jogosultság a mentéshez! (Nem adminként fut?)")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Váratlan hiba történt:\n{str(e)}")

if __name__ == "__main__":
    if platform.system() == "Windows": 
        run_as_admin()
        
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = HostsEditor()
    window.show()
    sys.exit(app.exec())
