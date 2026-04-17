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

#pragma once

#include <QWidget>
#include <QList>
#include <QString>
#include <QMap>
#include <QPoint>

#include <FCGlobal.h>

class QEvent;
class QKeyEvent;

namespace Gui {

class RibbonBar;


/// A single keytip badge: a letter label anchored to a specific widget.
struct KeyTipBadge
{
    QString key;            ///< The letter(s) to display (e.g. "H", "F2")
    QWidget* target;        ///< The widget this keytip activates
    QPoint   anchorOffset;  ///< Offset from target's top-left in ribbon coords
};


// ============================================================================
// RibbonKeyTip — Transparent overlay that shows keytip badges on the ribbon
//
//   Activated by pressing and releasing the Alt key (without combining with
//   another key).  Shows small badge labels on each ribbon tab and panel
//   button.  The user then presses the shown letter to navigate:
//
//     Alt → shows tab keytips (H=Home, V=View, D=Design, ...)
//     H   → activates Home tab, shows panel keytips within Home
//     P   → activates the "Pad" button
//     Esc → dismiss keytips at any level
//
//   §6.4 of MODERNIZATION_PLAN: "Keyboard tips — Alt+key reveals keytips
//   on all ribbon items.  RibbonKeyTip overlay system."
// ============================================================================

class GuiExport RibbonKeyTip : public QWidget
{
    Q_OBJECT

public:
    /// Construct the keytip overlay.  It installs itself as an event filter
    /// on the owning RibbonBar (and the top-level window for key capture).
    explicit RibbonKeyTip(RibbonBar* ribbon);
    ~RibbonKeyTip() override;

    /// Whether keytips are currently visible.
    bool isActive() const { return active_; }

    /// Programmatically show keytips at the tab level.
    void showTabKeyTips();

    /// Dismiss all keytips.
    void dismiss();

Q_SIGNALS:
    void keyTipsShown();
    void keyTipsDismissed();

protected:
    /// Paint the keytip badges on top of the ribbon.
    void paintEvent(QPaintEvent* event) override;

    /// Intercept Alt press/release and letter keys while active.
    bool eventFilter(QObject* watched, QEvent* event) override;

private:
    /// Build keytip badges for the tab bar.
    void buildTabKeyTips();

    /// Build keytip badges for buttons inside the current tab page.
    void buildPanelKeyTips();

    /// Assign unique single-letter keys (A-Z) to a set of widgets.
    /// Falls back to two-letter combos if more than 26.
    QMap<QWidget*, QString> assignKeys(const QList<QWidget*>& widgets) const;

    /// Activate the widget associated with a keytip string.
    void activateKeyTip(const QString& key);

    RibbonBar* ribbon_;
    bool active_ = false;

    enum Level { TabLevel, PanelLevel };
    Level currentLevel_ = TabLevel;

    QList<KeyTipBadge> badges_;
    QString pendingKey_;   ///< Accumulated multi-char key input
};


} // namespace Gui
