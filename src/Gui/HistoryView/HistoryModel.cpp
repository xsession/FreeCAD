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

#include <QApplication>
#include <QStyle>

#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/Property.h>
#include <App/PropertyStandard.h>
#include <App/PropertyLinks.h>
#include <App/SuppressibleExtension.h>
#include <Gui/Application.h>
#include <Gui/Document.h>
#include <Gui/ViewProvider.h>
#include <Gui/BitmapFactory.h>
#include <Gui/CommandT.h>

#include "HistoryModel.h"


using namespace Gui::HistoryView;
namespace sp = std::placeholders;

// ============================================================================
// Feature classification — Fusion 360-style families
// ============================================================================

FeatureFamily HistoryModel::classifyFeatureType(const QString& typeString)
{
    // Sketcher
    if (typeString.startsWith(QStringLiteral("Sketcher::"))
        || typeString.startsWith(QStringLiteral("PartDesign::Sketch"))) {
        return FeatureFamily::Sketch;
    }

    // PartDesign additive features
    if (typeString == QStringLiteral("PartDesign::Pad")
        || typeString == QStringLiteral("PartDesign::Revolution")
        || typeString == QStringLiteral("PartDesign::AdditivePipe")
        || typeString == QStringLiteral("PartDesign::AdditiveLoft")
        || typeString == QStringLiteral("PartDesign::AdditiveHelix")) {
        return FeatureFamily::Additive;
    }

    // PartDesign subtractive features
    if (typeString == QStringLiteral("PartDesign::Pocket")
        || typeString == QStringLiteral("PartDesign::Hole")
        || typeString == QStringLiteral("PartDesign::Groove")
        || typeString == QStringLiteral("PartDesign::SubtractivePipe")
        || typeString == QStringLiteral("PartDesign::SubtractiveLoft")
        || typeString == QStringLiteral("PartDesign::SubtractiveHelix")) {
        return FeatureFamily::Subtractive;
    }

    // PartDesign dress-up features
    if (typeString == QStringLiteral("PartDesign::Fillet")
        || typeString == QStringLiteral("PartDesign::Chamfer")
        || typeString == QStringLiteral("PartDesign::Draft")
        || typeString == QStringLiteral("PartDesign::Thickness")) {
        return FeatureFamily::DressUp;
    }

    // PartDesign transform features
    if (typeString == QStringLiteral("PartDesign::Mirrored")
        || typeString == QStringLiteral("PartDesign::LinearPattern")
        || typeString == QStringLiteral("PartDesign::PolarPattern")
        || typeString == QStringLiteral("PartDesign::MultiTransform")
        || typeString == QStringLiteral("PartDesign::Scaled")) {
        return FeatureFamily::Transform;
    }

    // PartDesign datum features
    if (typeString == QStringLiteral("PartDesign::Point")
        || typeString == QStringLiteral("PartDesign::Line")
        || typeString == QStringLiteral("PartDesign::Plane")
        || typeString == QStringLiteral("PartDesign::CoordinateSystem")) {
        return FeatureFamily::Datum;
    }

    // PartDesign boolean
    if (typeString == QStringLiteral("PartDesign::Boolean")) {
        return FeatureFamily::Boolean;
    }

    // PartDesign primitives (additive and subtractive)
    if (typeString.startsWith(QStringLiteral("PartDesign::Additive"))
        || typeString.startsWith(QStringLiteral("PartDesign::Subtractive"))) {
        return FeatureFamily::Primitive;
    }

    // Body
    if (typeString == QStringLiteral("PartDesign::Body")) {
        return FeatureFamily::Body;
    }

    // Part module features
    if (typeString.startsWith(QStringLiteral("Part::"))) {
        return FeatureFamily::Part;
    }

    return FeatureFamily::Unknown;
}


// ============================================================================
// HistoryEntry helpers
// ============================================================================

QIcon HistoryEntry::icon() const
{
    // Try feature-type-specific icon from BitmapFactory
    if (!objectType.isEmpty()) {
        static const QHash<QString, QString> iconMap = {
            {QStringLiteral("PartDesign::Pad"),              QStringLiteral("PartDesign_Pad")},
            {QStringLiteral("PartDesign::Pocket"),           QStringLiteral("PartDesign_Pocket")},
            {QStringLiteral("PartDesign::Revolution"),       QStringLiteral("PartDesign_Revolution")},
            {QStringLiteral("PartDesign::Groove"),           QStringLiteral("PartDesign_Groove")},
            {QStringLiteral("PartDesign::Fillet"),           QStringLiteral("PartDesign_Fillet")},
            {QStringLiteral("PartDesign::Chamfer"),          QStringLiteral("PartDesign_Chamfer")},
            {QStringLiteral("PartDesign::Draft"),            QStringLiteral("PartDesign_Draft")},
            {QStringLiteral("PartDesign::Thickness"),        QStringLiteral("PartDesign_Thickness")},
            {QStringLiteral("PartDesign::Hole"),             QStringLiteral("PartDesign_Hole")},
            {QStringLiteral("PartDesign::Mirrored"),         QStringLiteral("PartDesign_Mirrored")},
            {QStringLiteral("PartDesign::LinearPattern"),    QStringLiteral("PartDesign_LinearPattern")},
            {QStringLiteral("PartDesign::PolarPattern"),     QStringLiteral("PartDesign_PolarPattern")},
            {QStringLiteral("PartDesign::MultiTransform"),   QStringLiteral("PartDesign_MultiTransform")},
            {QStringLiteral("PartDesign::AdditivePipe"),     QStringLiteral("PartDesign_AdditivePipe")},
            {QStringLiteral("PartDesign::SubtractivePipe"),  QStringLiteral("PartDesign_SubtractivePipe")},
            {QStringLiteral("PartDesign::AdditiveLoft"),     QStringLiteral("PartDesign_AdditiveLoft")},
            {QStringLiteral("PartDesign::SubtractiveLoft"),  QStringLiteral("PartDesign_SubtractiveLoft")},
            {QStringLiteral("PartDesign::AdditiveHelix"),    QStringLiteral("PartDesign_AdditiveHelix")},
            {QStringLiteral("PartDesign::SubtractiveHelix"), QStringLiteral("PartDesign_SubtractiveHelix")},
            {QStringLiteral("PartDesign::Boolean"),          QStringLiteral("PartDesign_Boolean")},
            {QStringLiteral("PartDesign::Body"),             QStringLiteral("PartDesign_Body")},
            {QStringLiteral("PartDesign::Point"),            QStringLiteral("PartDesign_Point")},
            {QStringLiteral("PartDesign::Line"),             QStringLiteral("PartDesign_Line")},
            {QStringLiteral("PartDesign::Plane"),            QStringLiteral("PartDesign_Plane")},
            {QStringLiteral("PartDesign::CoordinateSystem"), QStringLiteral("PartDesign_CoordinateSystem")},
            {QStringLiteral("Sketcher::SketchObject"),       QStringLiteral("Sketcher_NewSketch")},
        };

        auto it = iconMap.find(objectType);
        if (it != iconMap.end()) {
            QPixmap pm = Gui::BitmapFactory().pixmap(it.value().toLatin1().constData());
            if (!pm.isNull()) {
                return QIcon(pm);
            }
        }
    }

    // Fallback to generic icons
    switch (type) {
    case EntryType::ObjectCreated:
        return QApplication::style()->standardIcon(QStyle::SP_FileIcon);
    case EntryType::ObjectDeleted:
        return QApplication::style()->standardIcon(QStyle::SP_TrashIcon);
    case EntryType::ObjectModified:
        return QApplication::style()->standardIcon(QStyle::SP_FileDialogDetailedView);
    case EntryType::Transaction:
        return QApplication::style()->standardIcon(QStyle::SP_CommandLink);
    case EntryType::Undo:
        return QApplication::style()->standardIcon(QStyle::SP_ArrowBack);
    case EntryType::Redo:
        return QApplication::style()->standardIcon(QStyle::SP_ArrowForward);
    case EntryType::Recompute:
        return QApplication::style()->standardIcon(QStyle::SP_BrowserReload);
    case EntryType::DocumentCreated:
        return QApplication::style()->standardIcon(QStyle::SP_FileDialogNewFolder);
    case EntryType::DocumentSaved:
        return QApplication::style()->standardIcon(QStyle::SP_DialogSaveButton);
    case EntryType::RollbackMarker:
        return QApplication::style()->standardIcon(QStyle::SP_MediaPlay);
    }
    return {};
}

QColor HistoryEntry::color() const
{
    // Fusion 360-style color coding by feature family
    switch (family) {
    case FeatureFamily::Sketch:      return QColor(0xFF, 0xA7, 0x26);  // orange/yellow
    case FeatureFamily::Additive:    return QColor(0x21, 0x96, 0xF3);  // blue
    case FeatureFamily::Subtractive: return QColor(0xF4, 0x43, 0x36);  // red
    case FeatureFamily::DressUp:     return QColor(0x4C, 0xAF, 0x50);  // green
    case FeatureFamily::Transform:   return QColor(0x9C, 0x27, 0xB0);  // purple
    case FeatureFamily::Datum:       return QColor(0x78, 0x78, 0x78);  // gray
    case FeatureFamily::Boolean:     return QColor(0xFF, 0x57, 0x22);  // deep orange
    case FeatureFamily::Primitive:   return QColor(0x00, 0x96, 0x88);  // teal
    case FeatureFamily::Body:        return QColor(0x1A, 0x23, 0x7E);  // dark blue
    case FeatureFamily::Part:        return QColor(0x29, 0x79, 0xFF);  // lighter blue
    case FeatureFamily::Document:    return QColor(0x00, 0xBC, 0xD4);  // cyan
    case FeatureFamily::UndoRedo:    return QColor(0x9E, 0x9E, 0x9E);  // gray
    case FeatureFamily::Unknown:
        break;
    }

    // Fallback to entry-type based colors
    switch (type) {
    case EntryType::ObjectCreated:    return QColor(0x4C, 0xAF, 0x50);
    case EntryType::ObjectDeleted:    return QColor(0xF4, 0x43, 0x36);
    case EntryType::ObjectModified:   return QColor(0xFF, 0x98, 0x00);
    case EntryType::Transaction:      return QColor(0x21, 0x96, 0xF3);
    case EntryType::Undo:             return QColor(0x9E, 0x9E, 0x9E);
    case EntryType::Redo:             return QColor(0x9E, 0x9E, 0x9E);
    case EntryType::Recompute:        return QColor(0x67, 0x3A, 0xB7);
    case EntryType::DocumentCreated:  return QColor(0x00, 0xBC, 0xD4);
    case EntryType::DocumentSaved:    return QColor(0x00, 0x96, 0x88);
    case EntryType::RollbackMarker:   return QColor(0xFF, 0xEB, 0x3B);
    }
    return QColor(0x9E, 0x9E, 0x9E);
}

QString HistoryEntry::typeLabel() const
{
    switch (type) {
    case EntryType::ObjectCreated:    return QObject::tr("Created");
    case EntryType::ObjectDeleted:    return QObject::tr("Deleted");
    case EntryType::ObjectModified:   return QObject::tr("Modified");
    case EntryType::Transaction:      return QObject::tr("Operation");
    case EntryType::Undo:             return QObject::tr("Undo");
    case EntryType::Redo:             return QObject::tr("Redo");
    case EntryType::Recompute:        return QObject::tr("Recompute");
    case EntryType::DocumentCreated:  return QObject::tr("New Document");
    case EntryType::DocumentSaved:    return QObject::tr("Saved");
    case EntryType::RollbackMarker:   return QObject::tr("Current State");
    }
    return {};
}

QString HistoryEntry::featureLabel() const
{
    if (objectType.isEmpty()) {
        return typeLabel();
    }

    // Strip namespace prefix for display (e.g. "PartDesign::Pad" -> "Pad")
    int colonIdx = objectType.lastIndexOf(QStringLiteral("::"));
    if (colonIdx >= 0) {
        return objectType.mid(colonIdx + 2);
    }
    return objectType;
}


// ============================================================================
// HistoryModel
// ============================================================================

HistoryModel::HistoryModel(QObject* parent)
    : QAbstractListModel(parent)
{
    coalesceTimer.setSingleShot(true);
    coalesceTimer.setInterval(100);
    connect(&coalesceTimer, &QTimer::timeout, this, &HistoryModel::flushPendingModification);
}

HistoryModel::~HistoryModel()
{
    detachDocument();
}

// ============================================================================
// Document attachment
// ============================================================================

void HistoryModel::setDocument(const App::Document* doc, const Gui::Document* gDoc)
{
    if (appDoc == doc) {
        return;
    }

    detachDocument();

    appDoc = doc;
    guiDoc = gDoc;

    if (!doc) {
        return;
    }

    // NOLINTBEGIN
    conNewObj = const_cast<App::Document*>(doc)->signalNewObject.connect(
        std::bind(&HistoryModel::onNewObject, this, sp::_1));
    conDelObj = const_cast<App::Document*>(doc)->signalDeletedObject.connect(
        std::bind(&HistoryModel::onDeletedObject, this, sp::_1));
    conChgObj = const_cast<App::Document*>(doc)->signalChangedObject.connect(
        std::bind(&HistoryModel::onChangedObject, this, sp::_1, sp::_2));
    conOpenTrans = const_cast<App::Document*>(doc)->signalOpenTransaction.connect(
        std::bind(&HistoryModel::onOpenTransaction, this, sp::_1, sp::_2));
    conCommitTrans = const_cast<App::Document*>(doc)->signalCommitTransaction.connect(
        std::bind(&HistoryModel::onCommitTransaction, this, sp::_1));
    conAbortTrans = const_cast<App::Document*>(doc)->signalAbortTransaction.connect(
        std::bind(&HistoryModel::onAbortTransaction, this, sp::_1));
    conUndo = const_cast<App::Document*>(doc)->signalUndo.connect(
        std::bind(&HistoryModel::onUndo, this, sp::_1));
    conRedo = const_cast<App::Document*>(doc)->signalRedo.connect(
        std::bind(&HistoryModel::onRedo, this, sp::_1));
    conRecomputed = const_cast<App::Document*>(doc)->signalRecomputed.connect(
        std::bind(&HistoryModel::onRecomputed, this, sp::_1, sp::_2));
    // NOLINTEND

    rebuildFromUndoStack();
}

void HistoryModel::detachDocument()
{
    conNewObj = {};
    conDelObj = {};
    conChgObj = {};
    conOpenTrans = {};
    conCommitTrans = {};
    conAbortTrans = {};
    conUndo = {};
    conRedo = {};
    conRecomputed = {};

    appDoc = nullptr;
    guiDoc = nullptr;
}

// ============================================================================
// QAbstractListModel interface
// ============================================================================

int HistoryModel::rowCount(const QModelIndex& parent) const
{
    if (parent.isValid()) {
        return 0;
    }
    return static_cast<int>(historyEntries.size());
}

QVariant HistoryModel::data(const QModelIndex& index, int role) const
{
    if (!index.isValid() || index.row() < 0
        || index.row() >= static_cast<int>(historyEntries.size())) {
        return {};
    }

    const auto& entry = historyEntries[index.row()];

    switch (role) {
    case Qt::DisplayRole:
        return entry.description;

    case Qt::DecorationRole:
        return entry.icon();

    case Qt::ForegroundRole:
        if (entry.isUndone) {
            return QColor(0x9E, 0x9E, 0x9E);
        }
        return {};

    case Qt::ToolTipRole: {
        // Rich tooltip — Fusion 360 style
        QString tip;
        if (!entry.featureLabel().isEmpty()) {
            tip += QStringLiteral("<b>%1</b>").arg(entry.featureLabel());
        }
        if (!entry.objectLabel.isEmpty()) {
            tip += QStringLiteral(" — %1").arg(entry.objectLabel);
        }
        tip += QStringLiteral("<br/><i>%1</i>").arg(entry.typeLabel());
        if (!entry.objectType.isEmpty()) {
            tip += QStringLiteral("<br/>Type: %1").arg(entry.objectType);
        }
        if (!entry.propertyName.isEmpty()) {
            tip += QStringLiteral("<br/>Property: %1").arg(entry.propertyName);
        }
        tip += QStringLiteral("<br/>Time: %1").arg(entry.timestamp.toString(Qt::ISODate));
        if (!entry.transactionName.isEmpty()) {
            tip += QStringLiteral("<br/>Transaction: %1").arg(entry.transactionName);
        }
        if (entry.isSuppressed) {
            tip += QStringLiteral("<br/><span style='color:red'>⊘ Suppressed</span>");
        }
        if (entry.isUndone) {
            tip += QStringLiteral("<br/><span style='color:gray'>Undone</span>");
        }
        return tip;
    }

    case EntryTypeRole:
        return static_cast<int>(entry.type);
    case ObjectNameRole:
        return entry.objectName;
    case ObjectLabelRole:
        return entry.objectLabel;
    case ObjectTypeRole:
        return entry.objectType;
    case PropertyNameRole:
        return entry.propertyName;
    case TransactionNameRole:
        return entry.transactionName;
    case TransactionIdRole:
        return entry.transactionId;
    case TimestampRole:
        return entry.timestamp;
    case IsUndoneRole:
        return entry.isUndone;
    case IsRollbackTargetRole:
        return entry.isRollbackTarget;
    case IsSuppressedRole:
        return entry.isSuppressed;
    case TypeLabelRole:
        return entry.typeLabel();
    case FeatureLabelRole:
        return entry.featureLabel();
    case FeatureFamilyRole:
        return static_cast<int>(entry.family);
    case ColorRole:
        return entry.color();
    case DescriptionRole:
        return entry.description;
    case GroupIdRole:
        return entry.groupId;
    }

    return {};
}

QHash<int, QByteArray> HistoryModel::roleNames() const
{
    auto roles = QAbstractListModel::roleNames();
    roles[EntryTypeRole]         = "entryType";
    roles[ObjectNameRole]        = "objectName";
    roles[ObjectLabelRole]       = "objectLabel";
    roles[ObjectTypeRole]        = "objectType";
    roles[PropertyNameRole]      = "propertyName";
    roles[TransactionNameRole]   = "transactionName";
    roles[TransactionIdRole]     = "transactionId";
    roles[TimestampRole]         = "timestamp";
    roles[IsUndoneRole]          = "isUndone";
    roles[IsRollbackTargetRole]  = "isRollbackTarget";
    roles[IsSuppressedRole]      = "isSuppressed";
    roles[TypeLabelRole]         = "typeLabel";
    roles[FeatureLabelRole]      = "featureLabel";
    roles[FeatureFamilyRole]     = "featureFamily";
    roles[ColorRole]             = "color";
    roles[DescriptionRole]       = "description";
    roles[GroupIdRole]           = "groupId";
    return roles;
}

// ============================================================================
// Timeline operations
// ============================================================================

bool HistoryModel::rollbackTo(int entryIndex)
{
    if (!appDoc || entryIndex < 0
        || entryIndex >= static_cast<int>(historyEntries.size())) {
        return false;
    }

    const auto& entry = historyEntries[entryIndex];

    if (entry.transactionId <= 0) {
        return false;
    }

    auto doc = const_cast<App::Document*>(appDoc);
    bool result = doc->undo(entry.transactionId);

    if (result) {
        updateRollbackMarkers();
    }

    return result;
}

void HistoryModel::clear()
{
    beginResetModel();
    historyEntries.clear();
    featureGroups.clear();
    rollbackPos = -1;
    endResetModel();
}

QString HistoryModel::exportToText() const
{
    QString result;
    result += QStringLiteral("=== FreeCAD Modification History ===\n");
    if (appDoc) {
        result += QStringLiteral("Document: %1\n").arg(QString::fromUtf8(appDoc->Label.getValue()));
    }
    result += QStringLiteral("Exported: %1\n").arg(QDateTime::currentDateTime().toString(Qt::ISODate));
    result += QStringLiteral("Total entries: %1\n\n").arg(historyEntries.size());

    int idx = 0;
    for (const auto& entry : historyEntries) {
        QString prefix = entry.isUndone      ? QStringLiteral("  [UNDONE] ")
                       : entry.isSuppressed  ? QStringLiteral("  [SUPPR]  ")
                       : entry.isRollbackTarget ? QStringLiteral("▶ ")
                                              : QStringLiteral("  ");
        result += QStringLiteral("%1%2  %3  [%4] %5\n")
                      .arg(prefix)
                      .arg(idx, 4)
                      .arg(entry.timestamp.toString(QStringLiteral("HH:mm:ss")))
                      .arg(entry.featureLabel())
                      .arg(entry.description);
        ++idx;
    }
    return result;
}

// ============================================================================
// Fusion 360-style operations
// ============================================================================

bool HistoryModel::editFeature(int entryIndex)
{
    if (!appDoc || !guiDoc || entryIndex < 0
        || entryIndex >= static_cast<int>(historyEntries.size())) {
        return false;
    }

    const auto& entry = historyEntries[entryIndex];
    if (entry.objectName.isEmpty()) {
        return false;
    }

    auto obj = appDoc->getObject(entry.objectName.toLatin1().constData());
    if (!obj) {
        return false;
    }

    // Use Gui::cmdSetEdit to open the feature's task panel
    try {
        Gui::cmdSetEdit(obj, 0);
        return true;
    }
    catch (...) {
        return false;
    }
}

bool HistoryModel::toggleSuppressed(int entryIndex)
{
    if (!appDoc || entryIndex < 0
        || entryIndex >= static_cast<int>(historyEntries.size())) {
        return false;
    }

    auto& entry = historyEntries[entryIndex];
    if (entry.objectName.isEmpty()) {
        return false;
    }

    auto obj = appDoc->getObject(entry.objectName.toLatin1().constData());
    if (!obj) {
        return false;
    }

    // Check if the object has the SuppressibleExtension
    auto ext = obj->getExtensionByType<App::SuppressibleExtension>(true);
    if (!ext) {
        return false;
    }

    bool newState = !ext->Suppressed.getValue();
    ext->Suppressed.setValue(newState);

    entry.isSuppressed = newState;
    QModelIndex idx = index(entryIndex);
    Q_EMIT dataChanged(idx, idx, {IsSuppressedRole});
    Q_EMIT suppressionChanged(entryIndex, newState);

    return true;
}

bool HistoryModel::isFeatureSuppressed(int entryIndex) const
{
    if (entryIndex < 0 || entryIndex >= static_cast<int>(historyEntries.size())) {
        return false;
    }
    return historyEntries[entryIndex].isSuppressed;
}

int HistoryModel::createGroup(const QString& name, int startIndex, int endIndex)
{
    if (startIndex < 0 || endIndex < startIndex
        || endIndex >= static_cast<int>(historyEntries.size())) {
        return -1;
    }

    FeatureGroup group;
    group.id = nextGroupId++;
    group.name = name;
    group.startIndex = startIndex;
    group.endIndex = endIndex;
    group.collapsed = false;

    for (int i = startIndex; i <= endIndex; ++i) {
        historyEntries[i].groupId = group.id;
    }

    featureGroups.push_back(group);

    Q_EMIT dataChanged(index(startIndex), index(endIndex), {GroupIdRole});

    return group.id;
}

void HistoryModel::removeGroup(int groupId)
{
    auto it = std::find_if(featureGroups.begin(), featureGroups.end(),
                           [groupId](const FeatureGroup& g) { return g.id == groupId; });
    if (it == featureGroups.end()) {
        return;
    }

    int startIdx = it->startIndex;
    int endIdx = it->endIndex;

    for (int i = startIdx; i <= endIdx
         && i < static_cast<int>(historyEntries.size()); ++i) {
        if (historyEntries[i].groupId == groupId) {
            historyEntries[i].groupId = -1;
        }
    }

    featureGroups.erase(it);

    Q_EMIT dataChanged(index(startIdx), index(endIdx), {GroupIdRole});
}

// ============================================================================
// Signal handlers
// ============================================================================

void HistoryModel::onNewObject(const App::DocumentObject& obj)
{
    if (coalesceTimer.isActive()) {
        flushPendingModification();
    }

    HistoryEntry entry;
    entry.type = EntryType::ObjectCreated;
    entry.objectType = QString::fromLatin1(obj.getTypeId().getName());
    entry.family = classifyFeatureType(entry.objectType);
    entry.description = tr("Created %1 (%2)")
                            .arg(QString::fromUtf8(obj.Label.getValue()),
                                 entry.featureLabel());
    entry.objectName = QString::fromLatin1(obj.getNameInDocument());
    entry.objectLabel = QString::fromUtf8(obj.Label.getValue());
    entry.timestamp = QDateTime::currentDateTime();

    // Check suppression state
    auto ext = const_cast<App::DocumentObject&>(obj)
                   .getExtensionByType<App::SuppressibleExtension>(true);
    if (ext) {
        entry.isSuppressed = ext->Suppressed.getValue();
    }

    if (insideTransaction) {
        entry.transactionName = currentTransactionName;
    }

    addEntry(std::move(entry));
}

void HistoryModel::onDeletedObject(const App::DocumentObject& obj)
{
    if (coalesceTimer.isActive()) {
        flushPendingModification();
    }

    HistoryEntry entry;
    entry.type = EntryType::ObjectDeleted;
    entry.objectType = QString::fromLatin1(obj.getTypeId().getName());
    entry.family = classifyFeatureType(entry.objectType);
    entry.description = tr("Deleted %1 (%2)")
                            .arg(QString::fromUtf8(obj.Label.getValue()),
                                 entry.featureLabel());
    entry.objectName = QString::fromLatin1(obj.getNameInDocument());
    entry.objectLabel = QString::fromUtf8(obj.Label.getValue());
    entry.timestamp = QDateTime::currentDateTime();

    if (insideTransaction) {
        entry.transactionName = currentTransactionName;
    }

    addEntry(std::move(entry));
}

void HistoryModel::onChangedObject(const App::DocumentObject& obj, const App::Property& prop)
{
    if (!shouldTrackProperty(prop)) {
        return;
    }

    QString objName = QString::fromLatin1(obj.getNameInDocument());
    QString propName = QString::fromLatin1(prop.getName());

    if (coalesceTimer.isActive() && pendingObjName == objName && pendingPropName == propName) {
        coalesceTimer.start();
        return;
    }

    if (coalesceTimer.isActive()) {
        flushPendingModification();
    }

    pendingObjName = objName;
    pendingPropName = propName;
    pendingDescription = describeProperty(obj, prop);
    coalesceTimer.start();
}

void HistoryModel::flushPendingModification()
{
    if (pendingObjName.isEmpty()) {
        return;
    }

    HistoryEntry entry;
    entry.type = EntryType::ObjectModified;
    entry.description = pendingDescription;
    entry.objectName = pendingObjName;
    entry.propertyName = pendingPropName;
    entry.timestamp = QDateTime::currentDateTime();

    if (appDoc) {
        auto obj = appDoc->getObject(pendingObjName.toLatin1().constData());
        if (obj) {
            entry.objectLabel = QString::fromUtf8(obj->Label.getValue());
            entry.objectType = QString::fromLatin1(obj->getTypeId().getName());
            entry.family = classifyFeatureType(entry.objectType);

            auto ext = obj->getExtensionByType<App::SuppressibleExtension>(true);
            if (ext) {
                entry.isSuppressed = ext->Suppressed.getValue();
            }
        }
    }

    if (insideTransaction) {
        entry.transactionName = currentTransactionName;
    }

    pendingObjName.clear();
    pendingPropName.clear();
    pendingDescription.clear();

    addEntry(std::move(entry));
}

void HistoryModel::onOpenTransaction(const App::Document& doc, std::string name)
{
    if (&doc != appDoc) {
        return;
    }

    insideTransaction = true;
    currentTransactionName = QString::fromStdString(name);
}

void HistoryModel::onCommitTransaction(const App::Document& doc)
{
    if (&doc != appDoc) {
        return;
    }

    if (coalesceTimer.isActive()) {
        flushPendingModification();
    }

    if (!currentTransactionName.isEmpty()) {
        HistoryEntry entry;
        entry.type = EntryType::Transaction;
        entry.family = FeatureFamily::Unknown;
        entry.description = tr("✓ %1").arg(currentTransactionName);
        entry.transactionName = currentTransactionName;
        entry.timestamp = QDateTime::currentDateTime();

        if (appDoc->getAvailableUndos() > 0) {
            entry.transactionId = appDoc->getTransactionID(true, 0);
        }

        addEntry(std::move(entry));
    }

    insideTransaction = false;
    currentTransactionName.clear();
}

void HistoryModel::onAbortTransaction(const App::Document& doc)
{
    if (&doc != appDoc) {
        return;
    }

    coalesceTimer.stop();
    pendingObjName.clear();
    pendingPropName.clear();
    pendingDescription.clear();

    insideTransaction = false;
    currentTransactionName.clear();
}

void HistoryModel::onUndo(const App::Document& doc)
{
    if (&doc != appDoc) {
        return;
    }

    HistoryEntry entry;
    entry.type = EntryType::Undo;
    entry.family = FeatureFamily::UndoRedo;

    auto redoNames = const_cast<App::Document*>(appDoc)->getAvailableRedoNames();
    if (!redoNames.empty()) {
        entry.description = tr("⟲ Undo: %1").arg(QString::fromStdString(redoNames.front()));
        entry.transactionName = QString::fromStdString(redoNames.front());
    }
    else {
        entry.description = tr("⟲ Undo");
    }

    entry.timestamp = QDateTime::currentDateTime();
    addEntry(std::move(entry));

    updateRollbackMarkers();
}

void HistoryModel::onRedo(const App::Document& doc)
{
    if (&doc != appDoc) {
        return;
    }

    HistoryEntry entry;
    entry.type = EntryType::Redo;
    entry.family = FeatureFamily::UndoRedo;

    auto undoNames = const_cast<App::Document*>(appDoc)->getAvailableUndoNames();
    if (!undoNames.empty()) {
        entry.description = tr("⟳ Redo: %1").arg(QString::fromStdString(undoNames.back()));
        entry.transactionName = QString::fromStdString(undoNames.back());
    }
    else {
        entry.description = tr("⟳ Redo");
    }

    entry.timestamp = QDateTime::currentDateTime();
    addEntry(std::move(entry));

    updateRollbackMarkers();
}

void HistoryModel::onRecomputed(const App::Document& doc,
                                 const std::vector<App::DocumentObject*>& objs)
{
    if (&doc != appDoc) {
        return;
    }

    if (objs.empty()) {
        return;
    }

    HistoryEntry entry;
    entry.type = EntryType::Recompute;
    entry.family = FeatureFamily::Unknown;
    if (objs.size() == 1) {
        entry.description = tr("Recomputed %1")
                                .arg(QString::fromUtf8(objs[0]->Label.getValue()));
        entry.objectName = QString::fromLatin1(objs[0]->getNameInDocument());
        entry.objectLabel = QString::fromUtf8(objs[0]->Label.getValue());
        entry.objectType = QString::fromLatin1(objs[0]->getTypeId().getName());
        entry.family = classifyFeatureType(entry.objectType);
    }
    else {
        entry.description = tr("Recomputed %1 objects").arg(objs.size());
    }
    entry.timestamp = QDateTime::currentDateTime();

    addEntry(std::move(entry));
}

// ============================================================================
// Helpers
// ============================================================================

void HistoryModel::addEntry(HistoryEntry entry)
{
    if (static_cast<int>(historyEntries.size()) >= MaxEntries) {
        beginRemoveRows(QModelIndex(), 0, 0);
        historyEntries.erase(historyEntries.begin());
        endRemoveRows();
    }

    int row = static_cast<int>(historyEntries.size());
    beginInsertRows(QModelIndex(), row, row);
    historyEntries.push_back(std::move(entry));
    endInsertRows();

    Q_EMIT entryAdded(row);
}

void HistoryModel::rebuildFromUndoStack()
{
    if (!appDoc) {
        return;
    }

    beginResetModel();
    historyEntries.clear();

    HistoryEntry docEntry;
    docEntry.type = EntryType::DocumentCreated;
    docEntry.family = FeatureFamily::Document;
    docEntry.description = tr("Document created: %1")
                               .arg(QString::fromUtf8(appDoc->Label.getValue()));
    docEntry.timestamp = QDateTime::currentDateTime();
    historyEntries.push_back(std::move(docEntry));

    auto undoNames = const_cast<App::Document*>(appDoc)->getAvailableUndoNames();

    for (int i = static_cast<int>(undoNames.size()) - 1; i >= 0; --i) {
        HistoryEntry entry;
        entry.type = EntryType::Transaction;
        entry.transactionName = QString::fromStdString(undoNames[i]);
        entry.description = tr("✓ %1").arg(entry.transactionName);
        entry.transactionId = appDoc->getTransactionID(true, i);
        entry.timestamp = QDateTime::currentDateTime();
        historyEntries.push_back(std::move(entry));
    }

    auto redoNames = const_cast<App::Document*>(appDoc)->getAvailableRedoNames();
    for (int i = static_cast<int>(redoNames.size()) - 1; i >= 0; --i) {
        HistoryEntry entry;
        entry.type = EntryType::Transaction;
        entry.transactionName = QString::fromStdString(redoNames[i]);
        entry.description = tr("✓ %1").arg(entry.transactionName);
        entry.transactionId = appDoc->getTransactionID(false, i);
        entry.isUndone = true;
        entry.timestamp = QDateTime::currentDateTime();
        historyEntries.push_back(std::move(entry));
    }

    endResetModel();

    updateRollbackMarkers();
}

void HistoryModel::updateRollbackMarkers()
{
    if (!appDoc) {
        return;
    }

    int redoCount = appDoc->getAvailableRedos();

    for (int i = 0; i < static_cast<int>(historyEntries.size()); ++i) {
        auto& e = historyEntries[i];
        bool wasTarget = e.isRollbackTarget;
        e.isRollbackTarget = false;

        if (wasTarget != e.isRollbackTarget) {
            QModelIndex idx = index(i);
            Q_EMIT dataChanged(idx, idx, {IsRollbackTargetRole, Qt::ForegroundRole});
        }
    }

    int transCount = 0;
    for (int i = static_cast<int>(historyEntries.size()) - 1; i >= 0; --i) {
        auto& e = historyEntries[i];
        if (e.type == EntryType::Transaction) {
            bool shouldBeUndone = transCount < redoCount;
            if (e.isUndone != shouldBeUndone) {
                e.isUndone = shouldBeUndone;
                QModelIndex idx = index(i);
                Q_EMIT dataChanged(idx, idx, {IsUndoneRole, Qt::ForegroundRole});
            }
            ++transCount;
        }
    }

    for (int i = static_cast<int>(historyEntries.size()) - 1; i >= 0; --i) {
        auto& e = historyEntries[i];
        if (e.type == EntryType::Transaction && !e.isUndone) {
            e.isRollbackTarget = true;
            rollbackPos = i;
            QModelIndex idx = index(i);
            Q_EMIT dataChanged(idx, idx, {IsRollbackTargetRole});
            Q_EMIT rollbackPositionChanged(i);
            break;
        }
    }
}

QString HistoryModel::describeObject(const App::DocumentObject& obj) const
{
    return QStringLiteral("%1 (%2)")
        .arg(QString::fromUtf8(obj.Label.getValue()),
             QString::fromLatin1(obj.getTypeId().getName()));
}

QString HistoryModel::describeProperty(const App::DocumentObject& obj,
                                        const App::Property& prop) const
{
    return tr("Modified %1.%2")
        .arg(QString::fromUtf8(obj.Label.getValue()),
             QString::fromLatin1(prop.getName()));
}

bool HistoryModel::shouldTrackProperty(const App::Property& prop) const
{
    const char* name = prop.getName();
    if (!name || !name[0]) {
        return false;
    }

    static const char* skipProps[] = {
        "Visibility",
        "DisplayMode",
        "SelectionStyle",
        "OnTopWhenSelected",
        "ShowInTree",
        "ShapeAppearance",
        "ExpressionEngine",
        nullptr
    };

    for (int i = 0; skipProps[i]; ++i) {
        if (strcmp(name, skipProps[i]) == 0) {
            return false;
        }
    }

    if (prop.testStatus(App::Property::Transient)
        || prop.testStatus(App::Property::Output)) {
        return false;
    }

    return true;
}
