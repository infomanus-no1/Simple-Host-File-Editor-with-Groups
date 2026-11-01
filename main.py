import sys
import os
import ctypes
import platform
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QLineEdit, QLabel, QMessageBox, QHeaderView, QPlainTextEdit, QDialog,
                             QMenu, QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem, 
                             QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut

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

# --- PROFI, MAGAS KONTRASZTÚ TÉMÁK (Modern Kék) ---
DARK_THEME = """
    QMainWindow, QDialog, QMessageBox, QMenu { background-color: #1E1E1E; color: #FFFFFF; }
    QWidget { color: #D4D4D4; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    QTreeWidget, QTableWidget { background-color: #252526; color: #D4D4D4; border: 1px solid #333333; border-radius: 6px; alternate-background-color: #2D2D30; gridline-color: #3E3E42; }
    QTreeWidget::item, QTableWidget::item { padding: 4px; }
    QTreeWidget::item:hover, QTableWidget::item:hover { background-color: #2A2D2E; }
    QTreeWidget::item:selected, QTableWidget::item:selected { background-color: #094771; color: #FFFFFF; }
    QHeaderView::section { background-color: #333333; color: #4DAAF1; padding: 6px; font-weight: bold; border: 1px solid #333333; }
    QPushButton { background-color: #0E639C; color: #FFFFFF; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; }
    QPushButton:hover { background-color: #1177BB; }
    QPushButton:pressed { background-color: #094771; color: #FFFFFF; }
    QLineEdit, QPlainTextEdit { background-color: #2D2D30; border: 1px solid #3E3E42; border-radius: 5px; padding: 6px; color: #FFFFFF; selection-background-color: #0E639C; selection-color: #FFFFFF; }
    QLabel { color: #FFFFFF; }
    QMenu::item:selected { background-color: #094771; color: #FFFFFF; }
"""

LIGHT_THEME = """
    QMainWindow, QDialog, QMessageBox, QMenu { background-color: #F3F3F3; color: #1E1E1E; }
    QWidget { color: #1E1E1E; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    QTreeWidget, QTableWidget { background-color: #FFFFFF; color: #1E1E1E; border: 1px solid #CCCCCC; border-radius: 6px; alternate-background-color: #F9F9F9; gridline-color: #E1E1E1; }
    QTreeWidget::item, QTableWidget::item { padding: 4px; }
    QTreeWidget::item:hover, QTableWidget::item:hover { background-color: #E8E8E8; }
    QTreeWidget::item:selected, QTableWidget::item:selected { background-color: #007ACC; color: #FFFFFF; }
    QHeaderView::section { background-color: #E1E1E1; color: #007ACC; padding: 6px; font-weight: bold; border: 1px solid #CCCCCC; }
    QPushButton { background-color: #007ACC; color: #FFFFFF; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; }
    QPushButton:hover { background-color: #0098FF; }
    QPushButton:pressed { background-color: #005A9E; color: #FFFFFF; }
    QLineEdit, QPlainTextEdit { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 5px; padding: 6px; color: #1E1E1E; selection-background-color: #007ACC; selection-color: #FFFFFF; }
    QLabel { color: #1E1E1E; }
    QMenu::item:selected { background-color: #007ACC; color: #FFFFFF; }
"""

class HostsEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Modern Hosts Szerkesztő (Intelligens Csoportosítás)")
        self.resize(1000, 750)
        self.is_dark = True
        self.old_item_text = ""
        
        # Beállítások
        self.grouping_mode = "base_tld" 
        self.custom_mapping = {}  # Ebbe mentjük az egyedi csoportsablonokat
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.apply_theme()
        self.load_hosts()

    def setup_ui(self):
        top_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP (pl. 127.0.0.1)")
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Domain (pl. teszt.local # megjegyzés)")
        
        add_btn = QPushButton("Hozzáadás")
        add_btn.clicked.connect(self.add_single_entry)
        bulk_btn = QPushButton("Tömeges")
        bulk_btn.clicked.connect(self.open_bulk_dialog)
        
        group_auto_btn = QPushButton("⚙️ Auto Csoport")
        group_auto_btn.clicked.connect(self.open_grouping_settings)
        
        group_custom_btn = QPushButton("📝 Egyedi Csoport")
        group_custom_btn.clicked.connect(self.open_custom_mapping_dialog)
        
        theme_btn = QPushButton("🌓 Téma")
        theme_btn.clicked.connect(self.toggle_theme)
        
        help_btn = QPushButton("ℹ️ Súgó")
        help_btn.clicked.connect(self.show_help)

        top_layout.addWidget(self.ip_input)
        top_layout.addWidget(self.host_input)
        top_layout.addWidget(add_btn)
        top_layout.addWidget(bulk_btn)
        top_layout.addWidget(group_auto_btn)
        top_layout.addWidget(group_custom_btn)
        top_layout.addWidget(theme_btn)
        top_layout.addWidget(help_btn)
        self.layout.addLayout(top_layout)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Kategória (Megjegyzés) ➔ IP Cím ➔ Domain"])
        
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
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

        QShortcut(QKeySequence("Delete"), self.tree, self.delete_selected)
        QShortcut(QKeySequence("Ctrl+C"), self.tree, self.copy_selected)

    # --- ÚJ/MÓDOSÍTOTT: Kategórianév megállapítása 2 lépcsőben ---
    def get_auto_category_name(self, clean_domain):
        """Kiszámolja, mi lenne a csoportneve az aktuális Auto (1/3) szabály szerint."""
        parts = clean_domain.split('.')
        if self.grouping_mode == "full":
            return clean_domain
            
        if len(parts) > 1:
            if self.grouping_mode == "base_only":
                return parts[-2]
            else:
                return '.'.join(parts[-2:])
                
        return clean_domain

    def get_category_name(self, domain):
        """Visszaadja a végleges kategóriát, figyelembe véve az egyedi felülírásokat."""
        clean_domain = domain.split(" #")[0].strip()
        
        # 1. Kiszámoljuk az automatikus alap kategóriát
        auto_cat = self.get_auto_category_name(clean_domain)
            
        # 2. Megnézzük, van-e ehhez az alap kategóriához egyedi (custom) leképezés megadva
        final_cat = self.custom_mapping.get(auto_cat, auto_cat)
            
        return final_cat if final_cat.startswith("#") else f"# {final_cat}"

    def rebuild_tree_from_memory(self):
        # 1. Összegyűjtjük a fáról a nem mentett jelenlegi állapotot is
        entries = []
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                ip_item = cat_item.child(j)
                ip = ip_item.text(0)
                for k in range(ip_item.childCount()):
                    domain = ip_item.child(k).text(0)
                    entries.append((ip, domain))
        
        # 2. Újraépítjük a belső struktúrát az új kategóriaszabályokkal
        structure = {}
        for ip, domain in entries:
            cat_name = self.get_category_name(domain)
            if cat_name not in structure:
                structure[cat_name] = {}
            if ip not in structure[cat_name]:
                structure[cat_name][ip] = set()
            structure[cat_name][ip].add(domain)
            
        # 3. GUI frissítése
        self.tree.blockSignals(True)
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        
        top_items = []
        cat_font = QFont()
        cat_font.setBold(True)
        cat_font.setPointSize(11)
        ip_font = QFont()
        ip_font.setItalic(True)
        cat_color = QColor("#4DAAF1") if self.is_dark else QColor("#007ACC")
        
        for cat_name, ips in structure.items():
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setFlags(cat_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cat_item.setFont(0, cat_font)
            cat_item.setForeground(0, cat_color)
            
            for ip, domains_set in ips.items():
                ip_item = QTreeWidgetItem([ip])
                ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
                ip_item.setFont(0, ip_font)
                cat_item.addChild(ip_item)
                
                for domain in domains_set:
                    domain_item = QTreeWidgetItem([domain])
                    domain_item.setFlags(domain_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    ip_item.addChild(domain_item)
                    
            top_items.append(cat_item)
            
        self.tree.addTopLevelItems(top_items)
        self.tree.expandAll()
        self.tree.setUpdatesEnabled(True)
        self.tree.blockSignals(False)

    def open_grouping_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Automatikus Csoportosítás")
        dialog.resize(350, 200)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Válaszd ki az automatikus kategóriaképzés módját:"))
        
        btn_group = QButtonGroup(dialog)
        
        radio_base_tld = QRadioButton("Fő domain + végződés (pl. example.com)")
        radio_base_only = QRadioButton("Csak a fő domain neve (pl. example)")
        radio_full = QRadioButton("Teljes domainnév (pl. dev.example.com)")
        
        btn_group.addButton(radio_base_tld)
        btn_group.addButton(radio_base_only)
        btn_group.addButton(radio_full)

        if self.grouping_mode == "base_only": radio_base_only.setChecked(True)
        elif self.grouping_mode == "full": radio_full.setChecked(True)
        else: radio_base_tld.setChecked(True)

        layout.addWidget(radio_base_tld)
        layout.addWidget(radio_base_only)
        layout.addWidget(radio_full)

        save_btn = QPushButton("Alkalmazás és Átrendezés")
        layout.addWidget(save_btn)

        def apply_settings():
            if radio_base_only.isChecked(): self.grouping_mode = "base_only"
            elif radio_full.isChecked(): self.grouping_mode = "full"
            else: self.grouping_mode = "base_tld"
            
            dialog.accept()
            self.rebuild_tree_from_memory()

        save_btn.clicked.connect(apply_settings)
        dialog.exec()

    # --- OKOSÍTOTT: Egyedi Csoportosítás Táblázat (csak a főcsoportokat listázza) ---
    def open_custom_mapping_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Egyedi Csoportnevek")
        dialog.resize(500, 500)
        layout = QVBoxLayout(dialog)
        
        info = QLabel("<b>Kategóriák egyedi elnevezése és összevonása</b><br>"
                      "A bal oszlop az aktuális <i>Auto Csoport</i> szabály alapján kiosztott neveket mutatja.<br>"
                      "Ha a jobb oszlopban többet is azonos névre írsz át, azok egyetlen mappába kerülnek!")
        layout.addWidget(info)
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Eredeti Főcsoport", "Egyedi Csoportnév"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setDefaultSectionSize(35)
        
        # Begyűjtjük az egyedi alapértelmezett kategória-neveket (a domének nélkül)
        auto_categories = set()
        for i in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                ip_item = cat_item.child(j)
                for k in range(ip_item.childCount()):
                    domain_full = ip_item.child(k).text(0)
                    clean_domain = domain_full.split(" #")[0].strip()
                    
                    # Kiszedjük a tiszta automatikus nevét a domainnek
                    auto_cat = self.get_auto_category_name(clean_domain)
                    auto_categories.add(auto_cat)

        # Sorok feltöltése ABC sorrendben
        table.setRowCount(len(auto_categories))
        for row, auto_cat in enumerate(sorted(auto_categories)):
            # Auto Kategória cella (nem szerkeszthető)
            orig_item = QTableWidgetItem(auto_cat)
            orig_item.setFlags(orig_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Egyedi Kategória cella (szerkeszthető) - Betölti, ha már adtunk neki korábban
            mapped_cat = self.custom_mapping.get(auto_cat, auto_cat)
            custom_item = QTableWidgetItem(mapped_cat)
            
            table.setItem(row, 0, orig_item)
            table.setItem(row, 1, custom_item)
            
        layout.addWidget(table)
        
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("✅ Alkalmazás és Újrarendezés")
        clear_btn = QPushButton("❌ Egyedi szabályok törlése")
        
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        def apply_custom_mapping():
            self.custom_mapping.clear()
            for r in range(table.rowCount()):
                orig = table.item(r, 0).text().strip()
                custom = table.item(r, 1).text().strip()
                # Csak azt mentjük el felülírásként, aminek tényleg más nevet adtunk
                if custom and custom != orig:
                    self.custom_mapping[orig] = custom
            dialog.accept()
            self.rebuild_tree_from_memory()
            
        def clear_mapping():
            self.custom_mapping.clear()
            dialog.accept()
            self.rebuild_tree_from_memory()
            
        apply_btn.clicked.connect(apply_custom_mapping)
        clear_btn.clicked.connect(clear_mapping)
        
        dialog.exec()

    def show_help(self):
        help_text = (
            "<h3>🚀 Modern Hosts Szerkesztő - Súgó</h3>"
            "<b>Csoportosítások:</b><br>"
            "<ul>"
            "<li><b>⚙️ Auto:</b> Automatikusan a domain végződés, név, vagy teljes név alapján rendezi mappába a sorokat.</li>"
            "<li><b>📝 Egyedi:</b> Itt szabadon, egy táblázatban nevezheted el, és vonhatod össze a főcsoportokat.</li>"
            "</ul>"
            "<b>Funkciók:</b><br>"
            "<ul>"
            "<li><b>Szerkesztés:</b> Kattints duplán bármelyik elemre a listában az átíráshoz.</li>"
            "<li><b>Törlés (Del gomb):</b> Jelölj ki elemeket és nyomj Delete-t. Automatikusan takarítja az üres mappákat is!</li>"
            "<li><b>Megjegyzések:</b> Egy sor megjegyzését fűzd hozzá a domainhez: <i>teszt.local # dev szerver</i></li>"
            "</ul>"
            "<p>A módosítások csak a <b>'Mentés a hosts fájlba'</b> gomb megnyomásakor íródnak ki a lemezre!</p>"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("Súgó és Használati Útmutató")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.exec()

    def show_context_menu(self, position):
        if not self.tree.selectedItems(): return
        menu = QMenu()
        copy_action = menu.addAction("📋 Másolás (Ctrl+C)")
        delete_action = menu.addAction("🗑️ Törlés (Del)")
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        if action == copy_action: self.copy_selected()
        elif action == delete_action: self.delete_selected()

    def copy_selected(self):
        items = self.tree.selectedItems()
        if items:
            QApplication.clipboard().setText("\n".join([item.text(0) for item in items]))

    def delete_selected(self):
        items = self.tree.selectedItems()
        if not items: return
        for item in items:
            if item.treeWidget() is None: continue
            parent = item.parent()
            if parent: parent.removeChild(item)
            else:
                idx = self.tree.indexOfTopLevelItem(item)
                if idx >= 0: self.tree.takeTopLevelItem(idx)

        for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
            cat_item = self.tree.topLevelItem(i)
            for j in range(cat_item.childCount() - 1, -1, -1):
                ip_item = cat_item.child(j)
                if ip_item.childCount() == 0: cat_item.removeChild(ip_item)
            if cat_item.childCount() == 0: self.tree.takeTopLevelItem(i)

    def apply_theme(self):
        theme = DARK_THEME if self.is_dark else LIGHT_THEME
        QApplication.instance().setStyleSheet(theme)
        cat_color = QColor("#4DAAF1") if self.is_dark else QColor("#007ACC")
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setForeground(0, cat_color)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()

    def load_hosts(self):
        if not os.path.exists(HOSTS_PATH): return
        
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        temp_entries = []
        current_category = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                current_category = ""
                continue
                
            if line.startswith("#"):
                if "Automatikus" not in line and "===" not in line and "---" not in line:
                    current_category = line
                continue
            
            inline_comment = ""
            if "#" in line:
                parts = line.split("#", 1)
                line = parts[0].strip()
                inline_comment = f" # {parts[1].strip()}"
                
            if not line: continue
                
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                domains = parts[1:]
                
                if inline_comment:
                    domains[-1] = f"{domains[-1]}{inline_comment}"
                
                for d in domains:
                    temp_entries.append((ip, d, current_category))

        structure = {}
        for ip, domain, saved_cat in temp_entries:
            cat_name = self.get_category_name(domain)
            
            if cat_name not in structure: structure[cat_name] = {}
            if ip not in structure[cat_name]: structure[cat_name][ip] = set()
            structure[cat_name][ip].add(domain)

        self.tree.blockSignals(True)
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        
        top_items = []
        cat_font, ip_font = QFont(), QFont()
        cat_font.setBold(True); cat_font.setPointSize(11)
        ip_font.setItalic(True)
        cat_color = QColor("#4DAAF1") if self.is_dark else QColor("#007ACC")

        for cat_name, ips in structure.items():
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setFlags(cat_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cat_item.setFont(0, cat_font)
            cat_item.setForeground(0, cat_color)
            
            for ip, domains_set in ips.items():
                ip_item = QTreeWidgetItem([ip])
                ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
                ip_item.setFont(0, ip_font)
                cat_item.addChild(ip_item)
                for d in domains_set:
                    domain_item = QTreeWidgetItem([d])
                    domain_item.setFlags(domain_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    ip_item.addChild(domain_item)
            top_items.append(cat_item)
            
        self.tree.addTopLevelItems(top_items)
        if len(temp_entries) < 1500: self.tree.expandAll()
        
        self.apply_theme()
        self.tree.setUpdatesEnabled(True)
        self.tree.blockSignals(False)

    def find_item(self, parent, text):
        if parent == self.tree:
            items = self.tree.findItems(text, Qt.MatchFlag.MatchExactly, 0)
            return items[0] if items else None
        for i in range(parent.childCount()):
            if parent.child(i).text(0) == text: return parent.child(i)
        return None

    def merge_into_tree(self, category, ip, domains):
        self.tree.blockSignals(True)
        cat_item = self.find_item(self.tree, category)
        if not cat_item:
            cat_item = QTreeWidgetItem([category])
            cat_item.setFlags(cat_item.flags() | Qt.ItemFlag.ItemIsEditable)
            cat_font = cat_item.font(0); cat_font.setBold(True); cat_font.setPointSize(11)
            cat_item.setFont(0, cat_font)
            cat_color = QColor("#4DAAF1") if self.is_dark else QColor("#007ACC")
            cat_item.setForeground(0, cat_color)
            self.tree.addTopLevelItem(cat_item)

        ip_item = self.find_item(cat_item, ip)
        if not ip_item:
            ip_item = QTreeWidgetItem([ip])
            ip_item.setFlags(ip_item.flags() | Qt.ItemFlag.ItemIsEditable)
            ip_font = ip_item.font(0); ip_font.setItalic(True)
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
            self.merge_into_tree(self.get_category_name(domain), ip, [domain])
            self.ip_input.clear()
            self.host_input.clear()
            self.tree.expandAll()

    def open_bulk_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Tömeges hozzáadás")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Minden sor egy bejegyzés legyen: IP Domain (pl. 127.0.0.1 teszt.local # komment)"))
        text_edit = QPlainTextEdit()
        btn = QPushButton("Feldolgozás")
        layout.addWidget(text_edit); layout.addWidget(btn)
        
        def process():
            self.tree.setUpdatesEnabled(False)
            for line in text_edit.toPlainText().split('\n'):
                line = line.strip()
                inline_comment = ""
                if "#" in line:
                    parts = line.split("#", 1)
                    line = parts[0].strip()
                    inline_comment = f" # {parts[1].strip()}"
                if not line: continue
                parts = line.split()
                if len(parts) >= 2:
                    ip, domains = parts[0], parts[1:]
                    if inline_comment: domains[-1] = f"{domains[-1]}{inline_comment}"
                    self.merge_into_tree(self.get_category_name(domains[0]), ip, domains)
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
                        for k in range(ip_item.childCount()):
                            f.write(f"{ip}\t{ip_item.child(k).text(0)}\n")
            QMessageBox.information(self, "Siker", "A hosts fájl sikeresen frissítve!")
        except PermissionError:
            QMessageBox.critical(self, "Hiba", "Nincs jogosultság a mentéshez! (Nem adminként fut?)")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"Váratlan hiba történt:\n{str(e)}")

if __name__ == "__main__":
    if platform.system() == "Windows": run_as_admin()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HostsEditor()
    window.show()
    sys.exit(app.exec())
