/***************************************************************************
 *   Copyright (c) 2024 FreeCAD Project                                   *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#include <QApplication>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QListWidget>
#include <QPainter>
#include <QPushButton>
#include <QHideEvent>
#include <QStackedWidget>
#include <QVBoxLayout>

#include "BackstageView.h"
#include "MainWindow.h"
#include "FileDialog.h"
#include "Command.h"
#include "RibbonBar.h"
#include "Workbench.h"
#include "WorkbenchManager.h"

using namespace Gui;

// ---------------------------------------------------------------------------
// BackstagePage
// ---------------------------------------------------------------------------

BackstagePage::BackstagePage(const QString& title, QWidget* parent)
    : QWidget(parent)
    , _title(title)
{
    _contentLayout = new QVBoxLayout(this);
    _contentLayout->setContentsMargins(24, 16, 24, 16);
    _contentLayout->setSpacing(12);

    // Page header
    auto* header = new QLabel(title, this);
    QFont headerFont = header->font();
    headerFont.setPointSize(18);
    headerFont.setBold(true);
    header->setFont(headerFont);
    _contentLayout->addWidget(header);

    _contentLayout->addStretch();
}

void BackstagePage::addAction(const QString& label,
                               const QString& iconPath,
                               const QString& description,
                               std::function<void()> callback)
{
    auto* btn = new QPushButton(this);
    btn->setIcon(QIcon(iconPath));
    btn->setIconSize(QSize(32, 32));
    btn->setText(label);
    btn->setToolTip(description);
    btn->setFlat(true);
    btn->setStyleSheet(
        QStringLiteral("QPushButton { text-align: left; padding: 8px 16px; font-size: 13px; }"
                        "QPushButton:hover { background: palette(highlight); color: palette(highlighted-text); }"));

    if (callback) {
        connect(btn, &QPushButton::clicked, this, [cb = std::move(callback)]() { cb(); });
    }

    // Insert before the stretch at the end
    _contentLayout->insertWidget(_contentLayout->count() - 1, btn);
}

void BackstagePage::addRecentFilesList()
{
    auto* recentLabel = new QLabel(tr("Recent Files"), this);
    QFont f = recentLabel->font();
    f.setBold(true);
    recentLabel->setFont(f);
    _contentLayout->insertWidget(_contentLayout->count() - 1, recentLabel);

    auto* list = new QListWidget(this);
    list->setMaximumHeight(300);

    // Populate from MainWindow recent files (limited read-only representation)
    // Actual integration would read the preference RecentFiles parameter group
    list->addItem(tr("(Recent files will appear here)"));
    _contentLayout->insertWidget(_contentLayout->count() - 1, list);
}

void BackstagePage::addWidget(QWidget* widget)
{
    if (widget) {
        _contentLayout->insertWidget(_contentLayout->count() - 1, widget);
    }
}

// ---------------------------------------------------------------------------
// BackstageView
// ---------------------------------------------------------------------------

BackstageView* BackstageView::_instance = nullptr;

BackstageView::BackstageView(QWidget* parent)
    : QWidget(parent)
{
    _instance = this;
    setObjectName(QStringLiteral("BackstageView"));
    buildLayout();
    hide(); // initially hidden
}

BackstageView::~BackstageView()
{
    if (_instance == this) {
        _instance = nullptr;
    }
}

BackstageView* BackstageView::instance()
{
    if (!_instance) {
        auto* mw = MainWindow::getInstance();
        _instance = new BackstageView(mw);
        _instance->setupDefaultPages();
    }
    return _instance;
}

BackstageView* BackstageView::existingInstance()
{
    return _instance;
}

void BackstageView::buildLayout()
{
    auto* mainLayout = new QHBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Left navigation panel (dark blue sidebar, ~220px)
    _navList = new QListWidget(this);
    _navList->setFixedWidth(220);
    _navList->setFrameShape(QFrame::NoFrame);
    _navList->setStyleSheet(
        QStringLiteral("QListWidget { background: #1a3a5c; color: white; font-size: 14px; }"
                        "QListWidget::item { padding: 12px 20px; }"
                        "QListWidget::item:selected { background: #2a5a8c; }"));
    mainLayout->addWidget(_navList);

    // Right content area
    auto* rightPanel = new QVBoxLayout();
    rightPanel->setContentsMargins(0, 0, 0, 0);

    _headerLabel = new QLabel(this);
    _headerLabel->setVisible(false); // header is inside each page

    _pageStack = new QStackedWidget(this);
    rightPanel->addWidget(_pageStack);

    mainLayout->addLayout(rightPanel, 1);

    connect(_navList, &QListWidget::currentItemChanged,
            this, &BackstageView::onPageSelected);
}

void BackstageView::addPage(const QString& name, BackstagePage* page)
{
    if (!page || _pages.contains(name)) {
        return;
    }
    _pages[name] = page;

    auto* item = new QListWidgetItem(name);
    item->setSizeHint(QSize(200, 48));
    _navList->addItem(item);

    _pageStack->addWidget(page);
}

void BackstageView::removePage(const QString& name)
{
    auto it = _pages.find(name);
    if (it == _pages.end()) {
        return;
    }
    _pageStack->removeWidget(it.value());
    _pages.erase(it);

    // Remove from nav list
    for (int i = 0; i < _navList->count(); ++i) {
        if (_navList->item(i)->text() == name) {
            delete _navList->takeItem(i);
            break;
        }
    }
}

void BackstageView::navigateTo(const QString& name)
{
    auto it = _pages.find(name);
    if (it != _pages.end()) {
        _pageStack->setCurrentWidget(it.value());
        // Update nav selection
        for (int i = 0; i < _navList->count(); ++i) {
            if (_navList->item(i)->text() == name) {
                _navList->setCurrentRow(i);
                break;
            }
        }
    }
}

void BackstageView::setupDefaultPages()
{
    auto closeBackstage = [this]() {
        hide();
        Q_EMIT closing();
    };

    // --- New ---
    auto* newPage = new BackstagePage(tr("New"), this);
    newPage->addAction(tr("Empty Document"), QStringLiteral(":/icons/document-new.svg"),
                        tr("Create a blank FreeCAD document"),
                        [closeBackstage]() {
                            Command::runCommand(Command::App, "FreeCAD.newDocument()");
                            closeBackstage();
                        });
    addPage(tr("New"), newPage);

    // --- Open ---
    auto* openPage = new BackstagePage(tr("Open"), this);
    openPage->addAction(tr("Browse..."), QStringLiteral(":/icons/document-open.svg"),
                         tr("Open an existing document"),
                         [closeBackstage]() {
                             // Trigger standard open command
                             Command::runCommand(Command::App, "Gui.runCommand('Std_Open')");
                             closeBackstage();
                         });
    openPage->addRecentFilesList();
    addPage(tr("Open"), openPage);

    // --- Save ---
    auto* savePage = new BackstagePage(tr("Save"), this);
    savePage->addAction(tr("Save"), QStringLiteral(":/icons/document-save.svg"),
                         tr("Save the active document"),
                         [closeBackstage]() {
                             Command::runCommand(Command::App, "Gui.runCommand('Std_Save')");
                             closeBackstage();
                         });
    savePage->addAction(tr("Save As..."), QStringLiteral(":/icons/document-save-as.svg"),
                         tr("Save the active document with a new name"),
                         [closeBackstage]() {
                             Command::runCommand(Command::App, "Gui.runCommand('Std_SaveAs')");
                             closeBackstage();
                         });
    addPage(tr("Save"), savePage);

    // --- Export ---
    auto* exportPage = new BackstagePage(tr("Export"), this);
    exportPage->addAction(tr("Export..."), QStringLiteral(":/icons/document-export.svg"),
                           tr("Export to STEP, IGES, STL, and more"),
                           [closeBackstage]() {
                               Command::runCommand(Command::App, "Gui.runCommand('Std_Export')");
                               closeBackstage();
                           });
    addPage(tr("Export"), exportPage);

    // --- Print ---
    auto* printPage = new BackstagePage(tr("Print"), this);
    printPage->addAction(tr("Print..."), QStringLiteral(":/icons/document-print.svg"),
                          tr("Print the current view or drawing"),
                          [closeBackstage]() {
                              Command::runCommand(Command::App, "Gui.runCommand('Std_Print')");
                              closeBackstage();
                          });
    addPage(tr("Print"), printPage);

    // --- Options ---
    auto* optionsPage = new BackstagePage(tr("Options"), this);
    optionsPage->addAction(tr("Preferences..."), QStringLiteral(":/icons/preferences-system.svg"),
                            tr("Open FreeCAD preferences"),
                            [closeBackstage]() {
                                Command::runCommand(Command::App,
                                    "Gui.runCommand('Std_DlgPreferences')");
                                closeBackstage();
                            });
    addPage(tr("Options"), optionsPage);

    // Select first page
    if (_navList->count() > 0) {
        _navList->setCurrentRow(0);
    }
}

void BackstageView::onPageSelected(QListWidgetItem* current, QListWidgetItem* /*previous*/)
{
    if (!current) {
        return;
    }
    auto it = _pages.find(current->text());
    if (it != _pages.end()) {
        _pageStack->setCurrentWidget(it.value());
    }
}

void BackstageView::showEvent(QShowEvent* event)
{
    QWidget::showEvent(event);

    // Resize to fill the parent (MainWindow central area)
    if (parentWidget()) {
        resize(parentWidget()->size());
        raise();
    }
}

void BackstageView::hideEvent(QHideEvent* event)
{
    QWidget::hideEvent(event);

    auto* ribbon = RibbonBar::instance();
    if (ribbon && RibbonBar::isRibbonEnabled()) {
        ribbon->show();
    }

    if (auto* workbench = WorkbenchManager::instance()->active()) {
        workbench->activate();
    }
}

void BackstageView::keyPressEvent(QKeyEvent* event)
{
    if (event->key() == Qt::Key_Escape) {
        hide();
        Q_EMIT closing();
        event->accept();
        return;
    }
    QWidget::keyPressEvent(event);
}

void BackstageView::paintEvent(QPaintEvent* event)
{
    QPainter painter(this);
    painter.fillRect(rect(), palette().window());
    QWidget::paintEvent(event);
}
