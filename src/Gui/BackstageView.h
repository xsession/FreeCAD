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
#include <QMap>
#include <QString>
#include <FCGlobal.h>

class QStackedWidget;
class QListWidget;
class QListWidgetItem;
class QVBoxLayout;
class QHBoxLayout;
class QLabel;

namespace Gui {

/// A page inside the BackstageView.  Each page represents a major
/// category such as "New", "Open", "Save", "Export", "Print", "Options".
class GuiExport BackstagePage : public QWidget
{
    Q_OBJECT

public:
    explicit BackstagePage(const QString& title, QWidget* parent = nullptr);

    const QString& pageTitle() const { return _title; }

    /// Add a labelled action button with icon
    void addAction(const QString& label, const QString& iconPath,
                   const QString& description, std::function<void()> callback);

    /// Add recent-files list (for the "Open" page)
    void addRecentFilesList();

    /// Add a custom widget section
    void addWidget(QWidget* widget);

private:
    QString _title;
    QVBoxLayout* _contentLayout = nullptr;
};

/// BackstageView — a full-screen overlay panel triggered by the "File" tab
/// in the RibbonBar.  Replaces the traditional File menu with a modern
/// full-page layout showing New / Open / Save / Export / Print / Options.
///
/// Usage:
///   BackstageView::instance()->show();  // opens the backstage
///   BackstageView::instance()->hide();  // returns to the CAD view
class GuiExport BackstageView : public QWidget
{
    Q_OBJECT

public:
    explicit BackstageView(QWidget* parent = nullptr);
    ~BackstageView() override;

    static BackstageView* instance();
    static BackstageView* existingInstance();

    /// Add a page. The first page added becomes the default selection.
    void addPage(const QString& name, BackstagePage* page);

    /// Remove a page by name.
    void removePage(const QString& name);

    /// Navigate to a specific page by name.
    void navigateTo(const QString& name);

    /// Set up the built-in pages (New, Open, Save, Export, Print, Options).
    void setupDefaultPages();

Q_SIGNALS:
    /// Emitted when the backstage is about to close
    void closing();

protected:
    void showEvent(QShowEvent* event) override;
    void hideEvent(QHideEvent* event) override;
    void keyPressEvent(QKeyEvent* event) override;
    void paintEvent(QPaintEvent* event) override;

private Q_SLOTS:
    void onPageSelected(QListWidgetItem* current, QListWidgetItem* previous);

private:
    void buildLayout();

    QListWidget* _navList = nullptr;
    QStackedWidget* _pageStack = nullptr;
    QLabel* _headerLabel = nullptr;
    QMap<QString, BackstagePage*> _pages;

    static BackstageView* _instance;
};

} // namespace Gui
