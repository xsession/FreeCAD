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

#include <QPainter>
#include <QPainterPath>
#include <QKeyEvent>
#include <QApplication>
#include <QTabWidget>
#include <QTabBar>
#include <QToolButton>
#include <QGridLayout>

#include "RibbonKeyTip.h"
#include "RibbonBar.h"

using namespace Gui;

// ---------------------------------------------------------------------------
// Style constants for keytip badges
// ---------------------------------------------------------------------------
namespace {
    constexpr int BadgePadH = 4;       // horizontal padding inside badge
    constexpr int BadgePadV = 2;       // vertical padding
    constexpr int BadgeRadius = 3;     // corner radius
    constexpr int BadgeFontSize = 9;   // point size
}

// ============================================================================
// Construction / destruction
// ============================================================================

RibbonKeyTip::RibbonKeyTip(RibbonBar* ribbon)
    : QWidget(ribbon)
    , ribbon_(ribbon)
{
    setAttribute(Qt::WA_TransparentForMouseEvents, false);
    setAttribute(Qt::WA_NoSystemBackground, true);
    setFocusPolicy(Qt::NoFocus);
    hide();

    // Install event filter on the top-level window to capture Alt key
    if (auto* topLevel = ribbon->window()) {
        topLevel->installEventFilter(this);
    }
}

RibbonKeyTip::~RibbonKeyTip()
{
    if (auto* topLevel = ribbon_->window()) {
        topLevel->removeEventFilter(this);
    }
}

// ============================================================================
// Public API
// ============================================================================

void RibbonKeyTip::showTabKeyTips()
{
    currentLevel_ = TabLevel;
    pendingKey_.clear();
    buildTabKeyTips();
    active_ = true;

    // Resize to cover the entire ribbon area
    setGeometry(ribbon_->rect());
    raise();
    show();
    Q_EMIT keyTipsShown();
}

void RibbonKeyTip::dismiss()
{
    active_ = false;
    badges_.clear();
    pendingKey_.clear();
    hide();
    Q_EMIT keyTipsDismissed();
}

// ============================================================================
// Paint keytip badges
// ============================================================================

void RibbonKeyTip::paintEvent(QPaintEvent* /*event*/)
{
    if (!active_ || badges_.isEmpty()) {
        return;
    }

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing, true);

    QFont badgeFont = font();
    badgeFont.setPointSize(BadgeFontSize);
    badgeFont.setBold(true);
    painter.setFont(badgeFont);

    QFontMetrics fm(badgeFont);

    for (const auto& badge : badges_) {
        if (!badge.target || !badge.target->isVisible()) {
            continue;
        }

        // Calculate badge position in our coordinate space
        QPoint targetPos = badge.target->mapTo(ribbon_, QPoint(0, 0));
        QPoint pos = targetPos + badge.anchorOffset;

        // Measure text
        QRect textRect = fm.boundingRect(badge.key);
        int w = textRect.width() + BadgePadH * 2;
        int h = fm.height() + BadgePadV * 2;
        QRect bgRect(pos.x() - w / 2, pos.y() - h / 2, w, h);

        // Badge background — light gold with dark border
        QPainterPath path;
        path.addRoundedRect(bgRect, BadgeRadius, BadgeRadius);

        painter.setPen(QPen(QColor(80, 80, 80), 1.0));
        painter.setBrush(QColor(255, 248, 220));  // cornsilk
        painter.drawPath(path);

        // Badge text
        painter.setPen(QColor(30, 30, 30));
        painter.drawText(bgRect, Qt::AlignCenter, badge.key);
    }
}

// ============================================================================
// Event filter — capture Alt and letter keys
// ============================================================================

bool RibbonKeyTip::eventFilter(QObject* watched, QEvent* event)
{
    if (event->type() == QEvent::KeyPress) {
        auto* ke = static_cast<QKeyEvent*>(event);

        // Alt alone pressed → show keytips (if not already active)
        if (ke->key() == Qt::Key_Alt && !active_) {
            // We show on Alt *release* if no other key was pressed
            return false;  // let the event propagate
        }

        if (active_) {
            if (ke->key() == Qt::Key_Escape) {
                if (currentLevel_ == PanelLevel) {
                    // Go back to tab level
                    showTabKeyTips();
                }
                else {
                    dismiss();
                }
                return true;
            }

            // Letter key input
            if (ke->key() >= Qt::Key_A && ke->key() <= Qt::Key_Z) {
                QString letter = QChar(QLatin1Char('A' + (ke->key() - Qt::Key_A)));
                pendingKey_ += letter;

                // Check for exact match
                bool hasExact = false;
                bool hasPrefix = false;
                for (const auto& badge : badges_) {
                    if (badge.key == pendingKey_) {
                        hasExact = true;
                    }
                    else if (badge.key.startsWith(pendingKey_) && badge.key != pendingKey_) {
                        hasPrefix = true;
                    }
                }

                if (hasExact && !hasPrefix) {
                    activateKeyTip(pendingKey_);
                    return true;
                }
                if (hasExact && hasPrefix) {
                    // Wait for more input or timeout
                    update();
                    return true;
                }
                if (!hasExact && !hasPrefix) {
                    // No match — dismiss
                    dismiss();
                    return true;
                }
                // Only prefix matches — wait for more
                update();
                return true;
            }

            // Any non-letter key dismisses keytips
            dismiss();
            return false;
        }
    }

    if (event->type() == QEvent::KeyRelease) {
        auto* ke = static_cast<QKeyEvent*>(event);

        // Alt released without any other key → show tab keytips
        if (ke->key() == Qt::Key_Alt && !active_
            && !(ke->modifiers() & ~Qt::AltModifier)) {
            showTabKeyTips();
            return true;
        }

        // Alt released while active → dismiss
        if (ke->key() == Qt::Key_Alt && active_) {
            // Don't dismiss on Alt release if we just showed keytips
            return false;
        }
    }

    // Mouse click anywhere dismisses keytips
    if (active_ && (event->type() == QEvent::MouseButtonPress
                    || event->type() == QEvent::MouseButtonDblClick)) {
        dismiss();
    }

    return QWidget::eventFilter(watched, event);
}

// ============================================================================
// Build keytip badge sets
// ============================================================================

void RibbonKeyTip::buildTabKeyTips()
{
    badges_.clear();

    // Find the tab bar inside the QTabWidget
    auto* tabWidget = ribbon_->findChild<QTabWidget*>();
    if (!tabWidget) {
        return;
    }
    QTabBar* tabBar = tabWidget->tabBar();
    if (!tabBar) {
        return;
    }

    // Collect tab widgets
    QList<QWidget*> tabTargets;
    for (int i = 0; i < tabBar->count(); ++i) {
        // We'll use the tabBar itself as the target; anchor at tab center
        tabTargets.append(tabBar);
    }

    // Assign keys: use first letter of tab text, fall back to indexing
    QMap<int, QString> usedKeys;
    QSet<QString> taken;

    for (int i = 0; i < tabBar->count(); ++i) {
        QString tabText = tabBar->tabText(i).toUpper().remove(QLatin1Char('&'));
        QString key;

        // Try first letter
        if (!tabText.isEmpty() && !taken.contains(tabText.left(1))) {
            key = tabText.left(1);
        }
        else {
            // Try other letters in the tab name
            for (int c = 1; c < tabText.length(); ++c) {
                QString candidate = tabText.mid(c, 1);
                if (candidate[0].isLetter() && !taken.contains(candidate)) {
                    key = candidate;
                    break;
                }
            }
        }

        // Fallback to number
        if (key.isEmpty()) {
            key = QString::number(i + 1);
        }

        taken.insert(key);

        KeyTipBadge badge;
        badge.key = key;
        badge.target = tabBar;

        // Position at center of the tab
        QRect tabRect = tabBar->tabRect(i);
        badge.anchorOffset = QPoint(tabRect.center().x(), tabRect.bottom() + 2);
        badges_.append(badge);
    }

    update();
}

void RibbonKeyTip::buildPanelKeyTips()
{
    badges_.clear();

    auto* tabWidget = ribbon_->findChild<QTabWidget*>();
    if (!tabWidget) {
        return;
    }

    QWidget* currentPage = tabWidget->currentWidget();
    if (!currentPage) {
        return;
    }

    // Find all QToolButtons in the current tab page
    QList<QToolButton*> buttons = currentPage->findChildren<QToolButton*>();
    QList<QWidget*> targets;
    for (auto* btn : buttons) {
        if (btn->isVisible() && btn->isEnabled()) {
            targets.append(btn);
        }
    }

    auto keyMap = assignKeys(targets);

    for (auto it = keyMap.begin(); it != keyMap.end(); ++it) {
        KeyTipBadge badge;
        badge.key = it.value();
        badge.target = it.key();
        // Anchor at bottom-center of button
        badge.anchorOffset = QPoint(it.key()->width() / 2,
                                    it.key()->height() - 2);
        badges_.append(badge);
    }

    update();
}

// ============================================================================
// Key assignment
// ============================================================================

QMap<QWidget*, QString> RibbonKeyTip::assignKeys(
    const QList<QWidget*>& widgets) const
{
    QMap<QWidget*, QString> result;
    QSet<QString> used;

    // First pass: try to assign single letters based on widget text
    for (auto* w : widgets) {
        auto* btn = qobject_cast<QToolButton*>(w);
        if (!btn) {
            continue;
        }
        QString text = btn->text().toUpper().remove(QLatin1Char('&'))
                           .remove(QLatin1Char('\n'));
        if (text.isEmpty()) {
            continue;
        }

        // Try first letter
        QString candidate = text.left(1);
        if (candidate[0].isLetter() && !used.contains(candidate)) {
            result.insert(w, candidate);
            used.insert(candidate);
        }
    }

    // Second pass: assign to widgets that didn't get a key
    for (auto* w : widgets) {
        if (result.contains(w)) {
            continue;
        }

        auto* btn = qobject_cast<QToolButton*>(w);
        QString text = btn ? btn->text().toUpper().remove(QLatin1Char('&'))
                                 .remove(QLatin1Char('\n'))
                           : QString();

        // Try remaining letters in text
        bool found = false;
        for (int c = 1; c < text.length() && !found; ++c) {
            if (text[c].isLetter()) {
                QString candidate = text.mid(c, 1);
                if (!used.contains(candidate)) {
                    result.insert(w, candidate);
                    used.insert(candidate);
                    found = true;
                }
            }
        }

        // Fallback: find any unused letter A-Z
        if (!found) {
            for (char ch = 'A'; ch <= 'Z'; ++ch) {
                QString candidate = QString(QLatin1Char(ch));
                if (!used.contains(candidate)) {
                    result.insert(w, candidate);
                    used.insert(candidate);
                    found = true;
                    break;
                }
            }
        }

        // Last resort: two-letter combo
        if (!found) {
            for (char c1 = 'A'; c1 <= 'Z'; ++c1) {
                for (char c2 = 'A'; c2 <= 'Z'; ++c2) {
                    QString candidate = QString(QLatin1Char(c1))
                                      + QString(QLatin1Char(c2));
                    if (!used.contains(candidate)) {
                        result.insert(w, candidate);
                        used.insert(candidate);
                        found = true;
                        break;
                    }
                }
                if (found) break;
            }
        }
    }

    return result;
}

// ============================================================================
// Activate a keytip
// ============================================================================

void RibbonKeyTip::activateKeyTip(const QString& key)
{
    for (const auto& badge : badges_) {
        if (badge.key == key) {
            if (currentLevel_ == TabLevel) {
                // Activate the tab
                auto* tabWidget = ribbon_->findChild<QTabWidget*>();
                if (tabWidget) {
                    QTabBar* tabBar = tabWidget->tabBar();
                    // Find which tab this badge corresponds to
                    for (int i = 0; i < badges_.size(); ++i) {
                        if (badges_[i].key == key) {
                            if (i < tabBar->count()) {
                                tabWidget->setCurrentIndex(i);
                            }
                            break;
                        }
                    }
                }
                // Drill down to panel level
                currentLevel_ = PanelLevel;
                pendingKey_.clear();
                buildPanelKeyTips();
                return;
            }

            if (currentLevel_ == PanelLevel) {
                // Click the button
                if (auto* btn = qobject_cast<QToolButton*>(badge.target)) {
                    dismiss();
                    btn->click();
                    return;
                }
            }
            break;
        }
    }

    // No match — dismiss
    dismiss();
}
