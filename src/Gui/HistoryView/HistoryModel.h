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

#pragma once

#include <QAbstractListModel>
#include <QDateTime>
#include <QIcon>
#include <QString>
#include <QTimer>

#include <fastsignals/signal.h>

#include <vector>
#include <memory>

namespace App {
class Document;
class DocumentObject;
class Property;
}

namespace Gui {
class Document;
class ViewProvider;

namespace HistoryView {

/// The type of modification that occurred
enum class EntryType {
    ObjectCreated,      ///< New feature/object added
    ObjectDeleted,      ///< Feature/object removed
    ObjectModified,     ///< Feature/object property changed
    Transaction,        ///< Named transaction (undo step)
    Undo,               ///< Undo operation
    Redo,               ///< Redo operation
    Recompute,          ///< Document recompute
    DocumentCreated,    ///< New document
    DocumentSaved,      ///< Document saved
    RollbackMarker      ///< Current rollback position marker
};

/// Feature family for Fusion 360-style color coding
enum class FeatureFamily {
    Unknown,          ///< Generic / unrecognized type
    Sketch,           ///< Sketcher operations — yellow/orange
    Additive,         ///< Additive geometry (Pad, Revolution, Loft…) — blue
    Subtractive,      ///< Subtractive geometry (Pocket, Groove…) — red/orange
    DressUp,          ///< Fillet, Chamfer, Draft, Thickness — green
    Transform,        ///< Pattern/Mirror/MultiTransform — purple
    Datum,            ///< Datum Point/Line/Plane/CS — gray
    Boolean,          ///< Boolean operations — orange
    Primitive,        ///< Additive/Subtractive primitives — teal
    Body,             ///< Body container — dark blue
    Document,         ///< Document-level events — cyan
    UndoRedo,         ///< Undo/Redo operations — gray
    Part              ///< Part module features — blue
};

/// A single entry in the modification history timeline
struct HistoryEntry {
    EntryType     type;
    FeatureFamily family{FeatureFamily::Unknown}; ///< Fusion 360-style feature family
    QString       description;      ///< Human-readable description
    QString       objectName;       ///< Name of the affected object (if applicable)
    QString       objectLabel;      ///< User-visible label of the object
    QString       objectType;       ///< Type string (e.g. "PartDesign::Pad")
    QString       propertyName;     ///< Changed property name (for ObjectModified)
    QString       transactionName;  ///< Transaction name from undo system
    int           transactionId{0}; ///< Transaction ID for rollback
    QDateTime     timestamp;        ///< When the modification occurred
    bool          isUndone{false};  ///< Whether this entry has been undone
    bool          isRollbackTarget{false}; ///< Whether this is the current rollback point
    bool          isSuppressed{false}; ///< Whether the feature is suppressed
    int           groupId{-1};      ///< Group index (-1 = no group)

    /// Get an icon for the entry type (feature-type-specific)
    QIcon icon() const;

    /// Get a color for the feature family (Fusion 360 color coding)
    QColor color() const;

    /// Get a short type label
    QString typeLabel() const;

    /// Get a short feature-type label (e.g. "Pad", "Fillet")
    QString featureLabel() const;
};


/// Custom roles for the model
enum HistoryRoles {
    EntryTypeRole = Qt::UserRole + 1,
    ObjectNameRole,
    ObjectLabelRole,
    ObjectTypeRole,
    PropertyNameRole,
    TransactionNameRole,
    TransactionIdRole,
    TimestampRole,
    IsUndoneRole,
    IsRollbackTargetRole,
    IsSuppressedRole,
    TypeLabelRole,
    FeatureLabelRole,
    FeatureFamilyRole,
    ColorRole,
    DescriptionRole,
    GroupIdRole
};


/// A named group of features on the timeline
struct FeatureGroup {
    int    id;          ///< Unique group ID
    QString name;       ///< Display name
    int    startIndex;  ///< First entry index in the group
    int    endIndex;    ///< Last entry index in the group
    bool   collapsed{false}; ///< Whether the group is collapsed in the UI
};


/**
 * @brief Qt model providing the modification history for a single document.
 *
 * Connects to App::Document and Gui::Application signals to track all
 * modifications in real-time — Fusion 360 "Design History" style.
 *
 * Features:
 *  - Records object creation, deletion, modification
 *  - Tracks named transactions (undo steps)
 *  - Supports rollback-to-point (undo to a specific transaction)
 *  - Marks undone entries visually
 *  - Provides a rollback marker showing current state
 *  - Auto-updates on undo/redo
 *  - Coalesces rapid property changes
 *  - Feature-family color coding (Fusion 360 style)
 *  - Suppress/unsuppress features
 *  - Feature grouping
 *  - Edit-feature support (opens task panel)
 */
class HistoryModel : public QAbstractListModel
{
    Q_OBJECT

public:
    explicit HistoryModel(QObject* parent = nullptr);
    ~HistoryModel() override;

    /// Attach to a document to start tracking
    void setDocument(const App::Document* doc, const Gui::Document* guiDoc);

    /// Detach from current document
    void detachDocument();

    /// Get the currently tracked document
    const App::Document* document() const { return appDoc; }

    // --- QAbstractListModel interface ---
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    QHash<int, QByteArray> roleNames() const override;

    // --- Timeline operations ---

    /// Rollback the document to the state at the given history entry index.
    bool rollbackTo(int entryIndex);

    /// Get the current rollback position (index of the marker)
    int rollbackPosition() const { return rollbackPos; }

    /// Clear all history entries
    void clear();

    /// Get all entries (read-only)
    const std::vector<HistoryEntry>& entries() const { return historyEntries; }

    /// Export history to a human-readable string
    QString exportToText() const;

    // --- Fusion 360-style operations ---

    /// Open the feature's edit dialog (like double-click in Fusion 360)
    bool editFeature(int entryIndex);

    /// Toggle suppress/unsuppress for a feature
    bool toggleSuppressed(int entryIndex);

    /// Check if a feature is suppressed
    bool isFeatureSuppressed(int entryIndex) const;

    /// Create a group from entries [startIndex, endIndex]
    int createGroup(const QString& name, int startIndex, int endIndex);

    /// Remove a group (ungroup)
    void removeGroup(int groupId);

    /// Get all groups
    const std::vector<FeatureGroup>& groups() const { return featureGroups; }

    /// Resolve the FeatureFamily for a given type string
    static FeatureFamily classifyFeatureType(const QString& typeString);

Q_SIGNALS:
    /// Emitted when the rollback position changes
    void rollbackPositionChanged(int newPos);

    /// Emitted when a new entry is added
    void entryAdded(int index);

    /// Emitted when a feature's suppression state changes
    void suppressionChanged(int entryIndex, bool suppressed);

private Q_SLOTS:
    /// Coalesce timer for rapid property changes
    void flushPendingModification();

private:
    // --- Signal handlers ---
    void onNewObject(const App::DocumentObject& obj);
    void onDeletedObject(const App::DocumentObject& obj);
    void onChangedObject(const App::DocumentObject& obj, const App::Property& prop);
    void onOpenTransaction(const App::Document& doc, std::string name);
    void onCommitTransaction(const App::Document& doc);
    void onAbortTransaction(const App::Document& doc);
    void onUndo(const App::Document& doc);
    void onRedo(const App::Document& doc);
    void onRecomputed(const App::Document& doc, const std::vector<App::DocumentObject*>& objs);

    // --- Helpers ---
    void addEntry(HistoryEntry entry);
    void rebuildFromUndoStack();
    void updateRollbackMarkers();
    QString describeObject(const App::DocumentObject& obj) const;
    QString describeProperty(const App::DocumentObject& obj, const App::Property& prop) const;
    bool shouldTrackProperty(const App::Property& prop) const;

    // --- Data ---
    const App::Document* appDoc{nullptr};
    const Gui::Document* guiDoc{nullptr};

    std::vector<HistoryEntry> historyEntries;
    std::vector<FeatureGroup> featureGroups;
    int rollbackPos{-1};  ///< Index of the current state marker (-1 = at end)
    int nextGroupId{0};   ///< Next group ID to assign

    // Signal connections (RAII)
    fastsignals::scoped_connection conNewObj;
    fastsignals::scoped_connection conDelObj;
    fastsignals::scoped_connection conChgObj;
    fastsignals::scoped_connection conOpenTrans;
    fastsignals::scoped_connection conCommitTrans;
    fastsignals::scoped_connection conAbortTrans;
    fastsignals::scoped_connection conUndo;
    fastsignals::scoped_connection conRedo;
    fastsignals::scoped_connection conRecomputed;

    // Coalescing for rapid property changes
    QTimer coalesceTimer;
    QString pendingObjName;
    QString pendingPropName;
    QString pendingDescription;
    bool insideTransaction{false};
    QString currentTransactionName;

    // Maximum entries to keep (prevents unbounded memory growth)
    static constexpr int MaxEntries = 10000;
};

} // namespace HistoryView
} // namespace Gui
