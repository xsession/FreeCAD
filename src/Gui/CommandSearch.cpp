// SPDX-License-Identifier: LGPL-2.1-or-later
/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
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
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"

#include "CommandSearch.h"

#include "Application.h"
#include "Action.h"
#include "BitmapFactory.h"
#include "Command.h"
#include "MainWindow.h"

#include <QAction>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QLabel>
#include <QShortcut>
#include <QVBoxLayout>

using namespace Gui;


// ════════════════════════════════════════════════════════════════════════
// Construction
// ════════════════════════════════════════════════════════════════════════

CommandSearch::CommandSearch(QWidget* parent)
    : QFrame(parent)
{
    setWindowFlags(Qt::Popup | Qt::FramelessWindowHint);
    setFrameShape(QFrame::StyledPanel);
    setFrameShadow(QFrame::Raised);
    setFixedWidth(PopupWidth);

    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(8, 8, 8, 8);
    layout->setSpacing(4);

    // Search input
    searchEdit = new QLineEdit(this);
    searchEdit->setPlaceholderText(tr("Type a command name..."));
    searchEdit->setClearButtonEnabled(true);
    searchEdit->installEventFilter(this);
    layout->addWidget(searchEdit);

    // Results list
    resultList = new QListWidget(this);
    resultList->setFocusPolicy(Qt::NoFocus);
    resultList->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    resultList->setSelectionMode(QAbstractItemView::SingleSelection);
    resultList->setIconSize(QSize(16, 16));
    layout->addWidget(resultList);

    connect(searchEdit, &QLineEdit::textChanged,
            this, &CommandSearch::onTextChanged);
    connect(resultList, &QListWidget::itemActivated,
            this, &CommandSearch::onItemActivated);
    connect(resultList, &QListWidget::itemClicked,
            this, &CommandSearch::onItemActivated);
}


// ════════════════════════════════════════════════════════════════════════
// Public API
// ════════════════════════════════════════════════════════════════════════

void CommandSearch::activate(const QString& initialText)
{
    buildCommandIndex();

    searchEdit->setText(initialText);
    searchEdit->selectAll();

    // Position centered above parent window
    if (auto* mw = MainWindow::getInstance()) {
        QPoint center = mw->geometry().center();
        int x = center.x() - PopupWidth / 2;
        int y = mw->geometry().top() + 80;  // Below ribbon area
        move(x, y);
    }

    show();
    raise();
    searchEdit->setFocus();

    updateResults(initialText);
}

void CommandSearch::registerShortcut()
{
    auto* mw = MainWindow::getInstance();
    if (!mw) {
        return;
    }

    auto* shortcut = new QShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_P), mw);
    QObject::connect(shortcut, &QShortcut::activated, [mw]() { openPalette(mw); });
}

void CommandSearch::openPalette(QWidget* parent, const QString& initialText)
{
    QWidget* owner = parent ? parent->window() : MainWindow::getInstance();
    if (!owner) {
        return;
    }

    static CommandSearch* instance = nullptr;
    if (!instance || instance->parentWidget() != owner) {
        instance = new CommandSearch(owner);
    }
    instance->activate(initialText);
}


// ════════════════════════════════════════════════════════════════════════
// Event handling
// ════════════════════════════════════════════════════════════════════════

bool CommandSearch::eventFilter(QObject* obj, QEvent* event)
{
    if (obj == searchEdit && event->type() == QEvent::KeyPress) {
        auto* ke = static_cast<QKeyEvent*>(event);
        switch (ke->key()) {
            case Qt::Key_Down:
                if (resultList->count() > 0) {
                    int row = resultList->currentRow();
                    resultList->setCurrentRow(std::min(row + 1, resultList->count() - 1));
                }
                return true;

            case Qt::Key_Up:
                if (resultList->count() > 0) {
                    int row = resultList->currentRow();
                    resultList->setCurrentRow(std::max(row - 1, 0));
                }
                return true;

            case Qt::Key_Return:
            case Qt::Key_Enter:
                if (auto* item = resultList->currentItem()) {
                    onItemActivated(item);
                }
                return true;

            case Qt::Key_Escape:
                hide();
                return true;

            default:
                break;
        }
    }
    return QFrame::eventFilter(obj, event);
}


// ════════════════════════════════════════════════════════════════════════
// Command Index
// ════════════════════════════════════════════════════════════════════════

void CommandSearch::buildCommandIndex()
{
    commandIndex.clear();

    auto& mgr = Application::Instance->commandManager();
    auto allCmds = mgr.getAllCommands();

    commandIndex.reserve(allCmds.size());

    for (auto* cmd : allCmds) {
        if (!cmd) {
            continue;
        }

        const char* menuText = cmd->getMenuText();
        if (!menuText || menuText[0] == '\0') {
            continue;
        }

        CommandEntry entry;
        entry.command = cmd;
        entry.displayName = QApplication::translate(cmd->className(), menuText);

        // Remove & accelerator markers from display name
        entry.displayName.remove(QLatin1Char('&'));

        const char* tooltip = cmd->getToolTipText();
        entry.searchText = entry.displayName.toLower();
        if (tooltip && tooltip[0] != '\0') {
            entry.searchText += QLatin1Char(' ')
                + QApplication::translate(cmd->className(), tooltip).toLower();
        }

        // Get keyboard shortcut if any
        if (auto* action = cmd->getAction()) {
            if (auto* qaction = action->action()) {
                QKeySequence seq = qaction->shortcut();
                if (!seq.isEmpty()) {
                    entry.shortcut = seq.toString(QKeySequence::NativeText);
                }
            }
        }

        commandIndex.push_back(std::move(entry));
    }
}


// ════════════════════════════════════════════════════════════════════════
// Search Logic
// ════════════════════════════════════════════════════════════════════════

void CommandSearch::onTextChanged(const QString& text)
{
    updateResults(text);
}

void CommandSearch::updateResults(const QString& query)
{
    resultList->clear();

    QString lowerQuery = query.trimmed().toLower();

    // Show top results when empty
    int count = 0;
    for (const auto& entry : commandIndex) {
        if (count >= MaxVisibleResults) {
            break;
        }

        if (!lowerQuery.isEmpty() && !fuzzyMatch(lowerQuery, entry.searchText)) {
            continue;
        }

        auto* item = new QListWidgetItem(resultList);

        // Display: "CommandName          Ctrl+X"
        QString text = entry.displayName;
        if (!entry.shortcut.isEmpty()) {
            text += QLatin1String("    ") + entry.shortcut;
        }
        item->setText(text);

        // Icon from command
        const char* pixmap = entry.command->getPixmap();
        if (pixmap && pixmap[0] != '\0') {
            item->setIcon(BitmapFactory().iconFromTheme(pixmap));
        }

        // Store command name for execution
        item->setData(Qt::UserRole, QString::fromLatin1(entry.command->getName()));

        ++count;
    }

    // Auto-select first result
    if (resultList->count() > 0) {
        resultList->setCurrentRow(0);
    }

    // Resize to fit content
    int itemHeight = resultList->sizeHintForRow(0);
    if (itemHeight <= 0) {
        itemHeight = 24;
    }
    int listHeight = std::min(resultList->count(), MaxVisibleResults) * itemHeight + 4;
    resultList->setFixedHeight(std::max(listHeight, itemHeight));
}

bool CommandSearch::fuzzyMatch(const QString& query, const QString& target) const
{
    // Subsequence match: all query characters must appear in order in target
    int qi = 0;
    int ti = 0;
    while (qi < query.length() && ti < target.length()) {
        if (query[qi] == target[ti]) {
            ++qi;
        }
        ++ti;
    }
    return qi == query.length();
}


// ════════════════════════════════════════════════════════════════════════
// Command Execution
// ════════════════════════════════════════════════════════════════════════

void CommandSearch::onItemActivated(QListWidgetItem* item)
{
    if (!item) {
        return;
    }

    QString cmdName = item->data(Qt::UserRole).toString();
    hide();

    if (!cmdName.isEmpty()) {
        auto& mgr = Application::Instance->commandManager();
        mgr.runCommandByName(cmdName.toLatin1().constData());
    }
}
