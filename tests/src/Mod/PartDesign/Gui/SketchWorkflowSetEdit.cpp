// SPDX-License-Identifier: LGPL-2.1-or-later
/**
 * Regression guard: verifies that Gui::Application::activateView()
 * is callable and handles the no-doc / no-view case safely.
 *
 * Background: PartDesignGui::setEdit() was fixed to call
 *   Gui::Application::Instance->activateView(View3DInventor::getClassTypeId(), true)
 * before querying the active view, so that a non-3D MDI window (e.g. the
 * Start page) can never "steal" focus and prevent the Sketch editor from
 * opening.
 */

#include <QTest>
#include <QDir>
#include <QFile>

#include "src/App/InitApplication.h"

#include <Gui/Application.h>
#include <Gui/View3DInventor.h>

class testSketchWorkflowSetEdit: public QObject
{
    Q_OBJECT

public:
    testSketchWorkflowSetEdit()
    {
        tests::initApplication();
    }

private:
    static void ensureGuiApplication()
    {
        if (!Gui::Application::Instance) {
            new Gui::Application(true);
        }
    }

private Q_SLOTS:

    void initTestCase()  // NOLINT
    {
        ensureGuiApplication();
    }

    // Guard test: activateView(View3DInventor, true) with no open document
    // must not crash. This is the exact call inserted at the top of
    // PartDesignGui::setEdit() as the Start-page focus-steal fix.
    void test_activateView_noCreate_isNoopWhenNoDocument()  // NOLINT
    {
        QVERIFY(Gui::Application::Instance->activeView() == nullptr);

        Gui::Application::Instance->activateView(
            Gui::View3DInventor::getClassTypeId(),
            true);

        QCoreApplication::processEvents();
        QVERIFY(Gui::Application::Instance->activeView() == nullptr);
    }

    // Compile-time guard: check signature used by the fix.
    void test_activateView_signatureGuard()  // NOLINT
    {
        auto guard = []() {
            Gui::Application::Instance->activateView(
                Gui::View3DInventor::getClassTypeId(),
                true);
        };
        Q_UNUSED(guard)
        QVERIFY(true);
    }

    // Source guard: ensure setEdit() still activates a 3D view before reading
    // activeView(). This protects against accidental reordering/removal.
    void test_setEdit_sourceContainsActivateViewBeforeActiveViewFetch()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString utilsPath = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/Utils.cpp"));
        QFile file(utilsPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(utilsPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString backstageNeedle = QStringLiteral("backstage->hide();");
        const QString activateNeedle =
            QStringLiteral("activateView(Gui::View3DInventor::getClassTypeId(), true)");
        const QString activeViewNeedle = QStringLiteral("auto* activeView = Gui::Application::Instance->activeView();");

        const int backstagePos = source.indexOf(backstageNeedle);
        const int activatePos = source.indexOf(activateNeedle);
        const int activeViewPos = source.indexOf(activeViewNeedle);

        QVERIFY2(backstagePos >= 0, "Backstage hide call missing in Utils.cpp::setEdit");
        QVERIFY2(activatePos >= 0, "activateView guard call missing in Utils.cpp::setEdit");
        QVERIFY2(activeViewPos >= 0, "activeView fetch line not found in Utils.cpp::setEdit");
        QVERIFY2(backstagePos < activatePos, "Backstage hide should run before activateView");
        QVERIFY2(activatePos < activeViewPos, "activateView guard must be before activeView fetch");
    }

    void test_sketchWorkflow_sourceActivates3DViewBeforeSetEdit()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString workflowPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/SketchWorkflow.cpp"));
        QFile file(workflowPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(workflowPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString createSketchNeedle = QStringLiteral("static void createSketch(");
        const QString activateNeedle
            = QStringLiteral("activateView(Gui::View3DInventor::getClassTypeId(), true)");
        const QString setEditNeedle = QStringLiteral("PartDesignGui::setEdit(Feat, partDesignBody);");

        const int createSketchPos = source.indexOf(createSketchNeedle);
        const int activatePos = source.indexOf(activateNeedle, createSketchPos);
        const int setEditPos = source.indexOf(setEditNeedle, createSketchPos);

        QVERIFY2(createSketchPos >= 0, "SketchWorkflow::createSketch helper not found");
        QVERIFY2(activatePos >= 0, "SketchWorkflow should activate a 3D view before setEdit");
        QVERIFY2(setEditPos >= 0, "SketchWorkflow setEdit call not found");
        QVERIFY2(activatePos < setEditPos,
                 "SketchWorkflow must activate a 3D view before setEdit");
    }

    void test_applicationActivateView_sourceSetsCreatedViewActive()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString appPath = repoRoot.filePath(QStringLiteral("src/Gui/Application.cpp"));
        QFile file(appPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(appPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString activateNeedle = QStringLiteral("void Application::activateView(const Base::Type& type, bool create)");
        const QString createNeedle = QStringLiteral("auto* createdView = doc->createView(type)");
        const QString setActiveNeedle = QStringLiteral("doc->setActiveWindow(createdView);");

        const int activatePos = source.indexOf(activateNeedle);
        const int createPos = source.indexOf(createNeedle, activatePos);
        const int setActivePos = source.indexOf(setActiveNeedle, activatePos);

        QVERIFY2(activatePos >= 0, "Application::activateView not found");
        QVERIFY2(createPos >= 0, "activateView should store the created view");
        QVERIFY2(setActivePos >= 0,
                 "activateView should set newly created view active when create=true");
        QVERIFY2(createPos < setActivePos,
                 "activateView should call setActiveWindow(createdView) after createView");
    }
};

QTEST_MAIN(testSketchWorkflowSetEdit)
#include "SketchWorkflowSetEdit.moc"
