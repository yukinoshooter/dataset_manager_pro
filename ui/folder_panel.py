from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QLineEdit
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path


class FolderPanel(QWidget):
    folders_changed = Signal(list)

    def __init__(self):
        super().__init__()

        self.root_path = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Include Folders"))

        #Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search folders...")
        self.search_input.textChanged.connect(self.filter_tree)
        layout.addWidget(self.search_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemChanged.connect(self.handle_item_changed)

        layout.addWidget(self.tree)

    def load_subfolders(self, folder_path):
        self.root_path = Path(folder_path)
        self.tree.clear()

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, self.root_path.name)
        root_item.setCheckState(0, Qt.Unchecked)
        root_item.setData(0, Qt.UserRole, str(self.root_path))

        self.add_children(root_item, self.root_path)

        self.tree.collapseAll()
        self.tree.expandItem(root_item)
        self.emit_selected_folders()

    def add_children(self, parent_item, parent_path):
        for sub in sorted(parent_path.iterdir()):
            if sub.is_dir():
                item = QTreeWidgetItem(parent_item)
                item.setText(0, sub.name)
                item.setCheckState(0, Qt.Unchecked)
                item.setData(0, Qt.UserRole, str(sub))

                self.add_children(item, sub)

    def handle_item_changed(self, item, column):
        state = item.checkState(0)

        # Apply state to children
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)

        self.emit_selected_folders()

    def emit_selected_folders(self):
        selected = []

        def traverse(item):
            if item.checkState(0) == Qt.Checked:
                selected.append(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                traverse(item.child(i))

        root = self.tree.topLevelItem(0)
        if root:
            traverse(root)

        self.folders_changed.emit(selected)

    def add_folder_to_tree(self, folder_path):
        """
        Add new folder to tree without rebuilding entire tree.
        """

        folder_path = Path(folder_path)

        # Recursive search for parent item
        def find_parent(item):
            if item.data(0, Qt.UserRole) == str(folder_path.parent):
                return item

            for i in range(item.childCount()):
                result = find_parent(item.child(i))
                if result:
                    return result

            return None

        root = self.tree.topLevelItem(0)
        if not root:
            return

        parent_item = find_parent(root)
        if not parent_item:
            return

        # Create new node
        new_item = QTreeWidgetItem(parent_item)
        new_item.setText(0, folder_path.name)
        new_item.setCheckState(0, Qt.Unchecked)
        new_item.setData(0, Qt.UserRole, str(folder_path))

        parent_item.setExpanded(True)

    def filter_tree(self, text):
        text = text.lower()

        def match_item(item):
            visible = text in item.text(0).lower()
            for i in range(item.childCount()):
                child = item.child(i)
                if match_item(child):
                    visible = True
            item.setHidden(not visible)
            return visible

        root = self.tree.topLevelItem(0)
        if root:
            match_item(root)