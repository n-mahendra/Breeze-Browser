import sys
import os
import json
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import *

BOOKMARKS_FILE = "bookmarks.json"
HISTORY_FILE = "history.txt"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)  

class DownloadItem(QWidget):
    def __init__(self, download):
        super().__init__()
        self.download = download
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel(download.path().split("/")[-1])
        self.progress = QProgressBar()
        self.status = QLabel("Starting...")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.status)

        download.downloadProgress.connect(self.update_progress)
        download.finished.connect(self.finish)

    def update_progress(self, received, total):
        if total > 0:
            progress = int((received / total) * 100)
            self.progress.setValue(progress)
            self.status.setText("Downloading...")

    def finish(self):
        self.status.setText("Done")

class DownloadManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 300, 600, 300)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def add_download(self, download):
        item = DownloadItem(download)
        self.layout.addWidget(item)

class BrowserTab(QWebEngineView):
    def __init__(self, parent, download_manager):
        super().__init__()
        self.parent = parent
        self.download_manager = download_manager
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.loadFinished.connect(self.save_history)

    def open_context_menu(self, pos):
        menu = QMenu(self)

        context_data = self.page().contextMenuData()

        # Check if clicked on a valid link
        if context_data.linkUrl().isValid():
            open_tab_action = menu.addAction("Open Link in New Tab")
            copy_link_action = menu.addAction("Copy Link Address")
            menu.addSeparator()

        back_action = menu.addAction("Back")
        forward_action = menu.addAction("Forward")
        reload_action = menu.addAction("Reload")
        copy_page_url_action = menu.addAction("Copy Page URL")

        action = menu.exec_(self.mapToGlobal(pos))

        # Handle link-specific actions
        if context_data.linkUrl().isValid():
            if action == open_tab_action:
                self.parent.add_new_tab(context_data.linkUrl(), "New Tab")
            elif action == copy_link_action:
                QApplication.clipboard().setText(context_data.linkUrl().toString())

        # Handle general browser actions
        if action == back_action:
            self.back()
        elif action == forward_action:
            self.forward()
        elif action == reload_action:
            self.reload()
        elif action == copy_page_url_action:
            QApplication.clipboard().setText(self.url().toString())

    def save_history(self):
        url = self.url().toString()
        with open(HISTORY_FILE, "a") as f:
            f.write(url + "\n")


class MainBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Breeze Browser")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(resource_path("icons/logo.png")))
        
        self.download_manager = DownloadManager()
        profile = QWebEngineProfile.defaultProfile()
        profile.downloadRequested.connect(self.on_download_requested)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar_from_tab)

        self.setCentralWidget(self.tabs)
        self.create_navbar()
        self.load_bookmarks()
        self.add_new_tab(QUrl("https://www.google.com"), "New Tab")



 

    def create_navbar(self):
        navbar = QToolBar()
        self.addToolBar(navbar)

        new_action = QAction(QIcon(resource_path("icons/plus.png")), "New Tab", self)
        new_action.triggered.connect( lambda: self.add_new_tab(QUrl("https://www.google.com")))
        navbar.addAction(new_action)


        back_action = QAction(QIcon(resource_path("icons/left-arrow.png")), "Back", self)
        back_action.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_action)

        forward_action = QAction(QIcon(resource_path("icons/right-arrow.png")), "Forward", self)
        forward_action.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_action)

        home_action = QAction(QIcon(resource_path("icons/home.png")), "Home", self)
        home_action.triggered.connect(lambda: self.current_browser().setUrl(QUrl("https://www.google.com")))
        navbar.addAction(home_action)        

        save_action = QAction(QIcon(resource_path("icons/star.png")), "Add Bookmark", self)
        save_action.triggered.connect(self.save_bookmark)
        navbar.addAction(save_action)

        download_action = QAction(QIcon(resource_path("icons/download.png")), "Downloads", self)
        download_action.triggered.connect(self.show_downloads)
        navbar.addAction(download_action)

        bookmarks_action = QAction(QIcon(resource_path("icons/bookmark.png")), "Bookmarks", self)
        bookmarks_action.triggered.connect(self.view_bookmarks)
        navbar.addAction(bookmarks_action)

        history_action = QAction(QIcon(resource_path("icons/cloud-computing")), "History", self)
        history_action.triggered.connect(self.view_history)
        navbar.addAction(history_action)

        aboutus_action = QAction(QIcon(resource_path("icons/question.png")), "About", self)
        aboutus_action.triggered.connect(self.show_about)
        navbar.addAction(aboutus_action)

        self.url_bar = QLineEdit()
        url_container = QWidget()
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_container.setLayout(url_layout)

        # Add icon (search/globe)
        #icon_label = QLabel()
        #icon_label.setPixmap(QPixmap("icons/globe.png").scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        #icon_label.setContentsMargins(8, 0, 4, 0)
      
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(36)
        self.url_bar.setStyleSheet("""
        QLineEdit {
        border: 1px solid #ccc;
        border-radius: 18px;
        padding-left: 10px;
        padding-right: 14px;
        font-size: 14px;
        background-color: #f1f3f4;
        color: #202124;
        }
        QLineEdit:hover {
        background-color: #ffffff;
        }
        QLineEdit:focus {
        border: 1px solid #1a73e8;
        background-color: #ffffff;
        }
        """)
        self.url_bar.returnPressed.connect(self.navigate_url)

        # Add icon + input to layout
        # url_layout.addWidget(icon_label)
        url_layout.addWidget(self.url_bar)
        navbar.addWidget(url_container)

        reload_action = QAction(QIcon(resource_path("icons/refresh.png")), "Reload", self)
        reload_action.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_action)

    def current_browser(self):
        return self.tabs.currentWidget()

    def update_urlbar_from_tab(self, index):
        browser = self.current_browser()
        if browser:
            self.url_bar.setText(browser.url().toString())

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl("https://www.google.com")

        browser = BrowserTab(self, self.download_manager)
        browser.setUrl(qurl)
        browser.urlChanged.connect(lambda q, b=browser: self.update_tab_title(b))
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def update_tab_title(self, browser):
        i = self.tabs.indexOf(browser)
        if i != -1:
            self.tabs.setTabText(i, browser.title())
        if self.current_browser() == browser:
            self.url_bar.setText(browser.url().toString())

    def close_tab(self, index):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(index)

    def navigate_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.current_browser().setUrl(QUrl(url))

    def save_bookmark(self):
        url = self.current_browser().url().toString()
        title = self.current_browser().title()

        bookmarks = []
        if os.path.exists(BOOKMARKS_FILE):
            with open(BOOKMARKS_FILE, 'r') as f:
                bookmarks = json.load(f)

        bookmarks.append({'title': title, 'url': url})
        with open(BOOKMARKS_FILE, 'w') as f:
            json.dump(bookmarks, f, indent=4)
        QMessageBox.information(self, "Bookmark Saved", f"Bookmarked: {title}")

    def load_bookmarks(self):
        if os.path.exists(BOOKMARKS_FILE):
            with open(BOOKMARKS_FILE, 'r') as f:
                self.bookmarks = json.load(f)
        else:
            self.bookmarks = []

    def view_bookmarks(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Bookmarks")
        layout = QVBoxLayout()

        for bm in self.bookmarks:
            btn = QPushButton(bm['title'])
            btn.clicked.connect(lambda _, url=bm['url']: self.current_browser().setUrl(QUrl(url)))
            layout.addWidget(btn)

        dlg.setLayout(layout)
        dlg.exec_()

    def view_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Browsing History")
        layout = QVBoxLayout()

        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                for line in f.readlines()[-20:][::-1]:
                    btn = QPushButton(line.strip())
                    btn.clicked.connect(lambda _, url=line.strip(): self.current_browser().setUrl(QUrl(url)))
                    layout.addWidget(btn)

        dlg.setLayout(layout)
        dlg.exec_()

    def show_about(self):
        QMessageBox.about(self, "About Us",
            "Breeze Browser\n"
            "Version: 26.06.089\n"
            "Build No: 20250607\n"
            "Features: Tabs, Bookmarks, History, Context Menu, Download Manager\n"
            "Built with PyQt5\n"
            "Developer: Mahendra.uk")

    def show_downloads(self):
        self.download_manager.show()

    def on_download_requested(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            download.setPath(path)
            download.accept()
            self.download_manager.add_download(download)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Breeze Browser")
    window = MainBrowser()
    window.show()
    sys.exit(app.exec_())
