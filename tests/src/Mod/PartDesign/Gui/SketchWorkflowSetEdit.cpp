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

#include <App/Application.h>
#include <App/Document.h>

#include <Gui/Application.h>
#include <Gui/Document.h>
#include <Gui/MDIView.h>
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

    static void closeAllDocuments()
    {
        App::GetApplication().closeAllDocuments();
        QCoreApplication::processEvents();
    }

private Q_SLOTS:

    void initTestCase()  // NOLINT
    {
        ensureGuiApplication();
        closeAllDocuments();
    }

    void cleanup()  // NOLINT
    {
        closeAllDocuments();
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

    // Runtime regression: when a document exists and create=true is requested,
    // activateView() must leave a 3D view active in the same call flow.
    void test_activateView_createMakes3DViewActiveOnDocument()  // NOLINT
    {
        const QByteArray platform = qgetenv("QT_QPA_PLATFORM");
        if (platform.compare("offscreen", Qt::CaseInsensitive) == 0
            || platform.compare("minimal", Qt::CaseInsensitive) == 0) {
            QSKIP("Runtime 3D-view activation check requires a real OpenGL-capable GUI platform");
        }

        App::Document* doc = App::GetApplication().newDocument("SketchWorkflowViewActivationDoc");
        QVERIFY(doc != nullptr);

        auto* guiDoc = Gui::Application::Instance->getDocument(doc);
        QVERIFY(guiDoc != nullptr);

        QVERIFY(Gui::Application::Instance->activeView() == nullptr);

        Gui::Application::Instance->activateView(
            Gui::View3DInventor::getClassTypeId(),
            true);

        QCoreApplication::processEvents();

        Gui::MDIView* activeView = Gui::Application::Instance->activeView();
        QVERIFY2(activeView != nullptr, "activateView(create=true) should yield an active view");
        QVERIFY2(activeView->isDerivedFrom(Gui::View3DInventor::getClassTypeId()),
                 "active view should be a 3D Inventor view");
    }

    // Source guard: ensure setEdit() still normalizes the sketch edit viewport
    // before reading activeView(). This protects against accidental reordering/removal.
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

        const QString viewportPrepNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(guiDocument);");
        const QString activeViewNeedle = QStringLiteral("auto* activeView = Gui::Application::Instance->activeView();");

        const int viewportPrepPos = source.indexOf(viewportPrepNeedle);
        const int activeViewPos = source.indexOf(activeViewNeedle);

        QVERIFY2(viewportPrepPos >= 0,
                 "Sketch workflow viewport normalization missing in Utils.cpp::setEdit");
        QVERIFY2(activeViewPos >= 0, "activeView fetch line not found in Utils.cpp::setEdit");
        QVERIFY2(viewportPrepPos < activeViewPos,
                 "Viewport normalization must happen before activeView fetch");
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
        const QString getDocumentNeedle
            = QStringLiteral("Application::Instance->getDocument(documentOfBody)");
        const QString prepareNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(guiDocument);");
        const QString setEditNeedle = QStringLiteral("PartDesignGui::setEdit(Feat, partDesignBody);");

        const int createSketchPos = source.indexOf(createSketchNeedle);
        const int getDocumentPos = source.indexOf(getDocumentNeedle, createSketchPos);
        const int preparePos = source.indexOf(prepareNeedle, createSketchPos);
        const int setEditPos = source.indexOf(setEditNeedle, createSketchPos);

        QVERIFY2(createSketchPos >= 0, "SketchWorkflow::createSketch helper not found");
        QVERIFY2(getDocumentPos >= 0,
                 "SketchWorkflow should resolve the GUI document before viewport normalization");
        QVERIFY2(preparePos >= 0,
                 "SketchWorkflow should use SketchWorkflowController viewport normalization before setEdit");
        QVERIFY2(setEditPos >= 0, "SketchWorkflow setEdit call not found");
        QVERIFY2(getDocumentPos < preparePos,
                 "SketchWorkflow should resolve the GUI document before viewport normalization");
        QVERIFY2(preparePos < setEditPos,
                 "SketchWorkflow should normalize the viewport before setEdit");
    }

    void test_sketcherEditCommand_routesThroughSketchWorkflowController()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString commandPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/Command.cpp"));
        QFile file(commandPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(commandPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString activatedNeedle
            = QStringLiteral("void CmdSketcherEditSketch::activated(int iMsg)");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::enterSketchEdit(");
        const QString directSetEditNeedle
            = QStringLiteral("Gui.activeDocument().setEdit('%s')");

        const int activatedPos = source.indexOf(activatedNeedle);
        const int controllerPos = source.indexOf(controllerNeedle, activatedPos);
        const int nextCommandPos = source.indexOf(
            QStringLiteral("bool CmdSketcherEditSketch::isActive()"), activatedPos);
        const int directSetEditPos = source.indexOf(directSetEditNeedle, activatedPos);

        QVERIFY2(activatedPos >= 0, "CmdSketcherEditSketch::activated not found");
        QVERIFY2(controllerPos >= 0,
                 "CmdSketcherEditSketch should call SketchWorkflowController");
        QVERIFY2(nextCommandPos >= 0, "CmdSketcherEditSketch::isActive not found");
        QVERIFY2(controllerPos < nextCommandPos,
                 "SketchWorkflowController call should be inside CmdSketcherEditSketch::activated");
        QVERIFY2(directSetEditPos < 0 || directSetEditPos > nextCommandPos,
                 "CmdSketcherEditSketch should not call Gui.activeDocument().setEdit directly");
    }

    void test_sketcherReorientCommand_routesThroughSketchWorkflowController()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString commandPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/Command.cpp"));
        QFile file(commandPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(commandPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString activatedNeedle
            = QStringLiteral("void CmdSketcherReorientSketch::activated(int iMsg)");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::enterSketchEdit(");
        const QString directSetEditNeedle
            = QStringLiteral("Gui.ActiveDocument.setEdit('%s')");

        const int activatedPos = source.indexOf(activatedNeedle);
        const int controllerPos = source.indexOf(controllerNeedle, activatedPos);
        const int nextCommandPos = source.indexOf(
            QStringLiteral("bool CmdSketcherReorientSketch::isActive()"), activatedPos);
        const int directSetEditPos = source.indexOf(directSetEditNeedle, activatedPos);

        QVERIFY2(activatedPos >= 0, "CmdSketcherReorientSketch::activated not found");
        QVERIFY2(controllerPos >= 0,
                 "CmdSketcherReorientSketch should call SketchWorkflowController");
        QVERIFY2(nextCommandPos >= 0, "CmdSketcherReorientSketch::isActive not found");
        QVERIFY2(controllerPos < nextCommandPos,
                 "SketchWorkflowController call should be inside CmdSketcherReorientSketch::activated");
        QVERIFY2(directSetEditPos < 0 || directSetEditPos > nextCommandPos,
                 "CmdSketcherReorientSketch should not call Gui.ActiveDocument.setEdit directly");
    }

    void test_sketcherNewSketch_routesCreatedSketchThroughSketchWorkflowController()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString commandPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/Command.cpp"));
        QFile file(commandPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(commandPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString activatedNeedle
            = QStringLiteral("void CmdSketcherNewSketch::activated(int iMsg)");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::enterSketchEdit(");
        const QString nextCommandNeedle = QStringLiteral("bool CmdSketcherNewSketch::isActive()");
        const QString directSetEditNeedle
            = QStringLiteral("Gui.activeDocument().setEdit('%s')");

        const int activatedPos = source.indexOf(activatedNeedle);
        const int firstControllerPos = source.indexOf(controllerNeedle, activatedPos);
        const int secondControllerPos = source.indexOf(controllerNeedle, firstControllerPos + 1);
        const int nextCommandPos = source.indexOf(nextCommandNeedle, activatedPos);
        const int directSetEditPos = source.indexOf(directSetEditNeedle, activatedPos);

        QVERIFY2(activatedPos >= 0, "CmdSketcherNewSketch::activated not found");
        QVERIFY2(firstControllerPos >= 0,
                 "CmdSketcherNewSketch should route sketch entry through SketchWorkflowController");
        QVERIFY2(secondControllerPos >= 0,
                 "CmdSketcherNewSketch should route both attached and detached sketch paths through SketchWorkflowController");
        QVERIFY2(nextCommandPos >= 0, "CmdSketcherNewSketch::isActive not found");
        QVERIFY2(firstControllerPos < nextCommandPos && secondControllerPos < nextCommandPos,
                 "SketchWorkflowController calls should be inside CmdSketcherNewSketch::activated");
        QVERIFY2(directSetEditPos < 0 || directSetEditPos > nextCommandPos,
                 "CmdSketcherNewSketch should not call Gui.activeDocument().setEdit directly");
    }

    void test_sketcherDoubleClick_routesThroughSketchWorkflowController()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString providerPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/ViewProviderSketch.cpp"));
        QFile file(providerPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(providerPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString doubleClickedNeedle = QStringLiteral("bool ViewProviderSketch::doubleClicked()");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::enterSketchEdit(");
        const QString directSetEditNeedle
            = QStringLiteral("activeDocument()->setEdit(this)");
        const QString nextMethodNeedle = QStringLiteral("float ViewProviderSketch::getScaleFactor() const");

        const int doubleClickedPos = source.indexOf(doubleClickedNeedle);
        const int controllerPos = source.indexOf(controllerNeedle, doubleClickedPos);
        const int nextMethodPos = source.indexOf(nextMethodNeedle, doubleClickedPos);
        const int directSetEditPos = source.indexOf(directSetEditNeedle, doubleClickedPos);

        QVERIFY2(doubleClickedPos >= 0, "ViewProviderSketch::doubleClicked not found");
        QVERIFY2(controllerPos >= 0,
                 "ViewProviderSketch::doubleClicked should call SketchWorkflowController");
        QVERIFY2(nextMethodPos >= 0, "ViewProviderSketch::getScaleFactor not found");
        QVERIFY2(controllerPos < nextMethodPos,
                 "SketchWorkflowController call should be inside ViewProviderSketch::doubleClicked");
        QVERIFY2(directSetEditPos < 0 || directSetEditPos > nextMethodPos,
                 "ViewProviderSketch::doubleClicked should not call setEdit directly");
    }

    void test_sketchWorkflowController_sourceNormalizesBackstageAnd3DView()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString controllerPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/SketchWorkflowController.cpp"));
        QFile file(controllerPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(controllerPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString helperNeedle = QStringLiteral("void normalizeSketchIntentViewport(");
        const QString backstageNeedle = QStringLiteral("backstage->hide();");
        const QString setActiveViewNeedle
            = QStringLiteral("setActiveView(nullptr, Gui::View3DInventor::getClassTypeId())");
        const QString activateNeedle
            = QStringLiteral("activateView(Gui::View3DInventor::getClassTypeId(), true)");

        const int helperPos = source.indexOf(helperNeedle);
        const int backstagePos = source.indexOf(backstageNeedle, helperPos);
        const int setActiveViewPos = source.indexOf(setActiveViewNeedle, helperPos);
        const int activatePos = source.indexOf(activateNeedle, helperPos);

        QVERIFY2(helperPos >= 0, "normalizeSketchIntentViewport helper not found");
        QVERIFY2(backstagePos >= 0,
                 "SketchWorkflowController should hide backstage before entering sketch edit");
        QVERIFY2(setActiveViewPos >= 0,
                 "SketchWorkflowController should force a 3D document view before entering sketch edit");
        QVERIFY2(activatePos >= 0,
                 "SketchWorkflowController should activate a 3D view before entering sketch edit");
        QVERIFY2(backstagePos < setActiveViewPos,
                 "Backstage should be hidden before forcing the 3D document view");
        QVERIFY2(setActiveViewPos < activatePos,
                 "SketchWorkflowController should choose a 3D document view before activating it");
    }

    void test_partDesignSetEdit_usesSketchWorkflowViewportNormalization()  // NOLINT
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

        const QString setEditNeedle = QStringLiteral("bool setEdit(App::DocumentObject* obj, PartDesign::Body* body)");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(guiDocument);");
        const QString activateWorkbenchNeedle
            = QStringLiteral("activateWorkbench(\"SketcherWorkbench\")");

        const int setEditPos = source.indexOf(setEditNeedle);
        const int controllerPos = source.indexOf(controllerNeedle, setEditPos);
        const int activateWorkbenchPos = source.indexOf(activateWorkbenchNeedle, setEditPos);

        QVERIFY2(setEditPos >= 0, "PartDesignGui::setEdit not found in Utils.cpp");
        QVERIFY2(controllerPos >= 0,
                 "PartDesignGui::setEdit should use SketchWorkflowController viewport normalization");
        QVERIFY2(activateWorkbenchPos >= 0,
                 "PartDesignGui::setEdit should explicitly activate SketcherWorkbench for sketch targets");
        QVERIFY2(controllerPos < activateWorkbenchPos,
                 "Viewport normalization should happen before sketch workbench activation");
    }

    void test_partDesignNewSketchCommand_usesSketchWorkflowViewportNormalization()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString commandPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/Command.cpp"));
        QFile file(commandPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(commandPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString activatedNeedle
            = QStringLiteral("void CmdPartDesignNewSketch::activated(int iMsg)");
        const QString controllerNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(getActiveGuiDocument())");
        const QString createWorkflowNeedle
            = QStringLiteral("PartDesignGui::SketchWorkflow creator(getActiveGuiDocument());");

        const int activatedPos = source.indexOf(activatedNeedle);
        const int controllerPos = source.indexOf(controllerNeedle, activatedPos);
        const int createWorkflowPos = source.indexOf(createWorkflowNeedle, activatedPos);

        QVERIFY2(activatedPos >= 0, "CmdPartDesignNewSketch::activated not found");
        QVERIFY2(controllerPos >= 0,
                 "CmdPartDesignNewSketch should use SketchWorkflowController viewport normalization");
        QVERIFY2(createWorkflowPos >= 0, "PartDesign sketch workflow creation call not found");
        QVERIFY2(controllerPos < createWorkflowPos,
                 "Viewport normalization should happen before PartDesign sketch creation begins");
    }

    void test_partDesignWorkbench_taskWatchers_requireActiveBodyMembership()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString workbenchPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/Workbench.cpp"));
        QFile file(workbenchPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(workbenchPath));
        const QString source = QString::fromUtf8(file.readAll());

        QVERIFY2(source.contains(QStringLiteral("class ActiveBodySelectionWatcher")),
             "PartDesign workbench should define an active-body-aware selection watcher");
        QVERIFY2(source.contains(QStringLiteral("PartDesignGui::getBody(false)")),
                 "ActiveBodySelectionWatcher should resolve the active PartDesign body");
        QVERIFY2(source.contains(QStringLiteral("PartDesign::Body::findBodyOf(sel.pObject) != activeBody")),
                 "ActiveBodySelectionWatcher should reject selections outside the active body");
        QVERIFY2(source.contains(QStringLiteral("new ActiveBodySelectionWatcher("))
                 && source.contains(QStringLiteral("\"SELECT Sketcher::SketchObject COUNT 1\"")),
                 "Single-sketch modeling tools should require active-body membership");
        QVERIFY2(source.contains(QStringLiteral("\"SELECT PartDesign::SketchBased\"")),
                 "Transformation tools should require active-body membership");
    }

    void test_partDesignFeatureDialogs_publishTaskViewContextMetadata()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString taskFeaturePath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/TaskFeatureParameters.cpp"));
        QFile file(taskFeaturePath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(taskFeaturePath));
        const QString source = QString::fromUtf8(file.readAll());

        QVERIFY2(source.contains(QStringLiteral("void TaskDlgFeatureParameters::updateTaskViewMetadata()")),
                 "PartDesign feature dialogs should centralize task-view metadata publication");
        QVERIFY2(source.contains(QStringLiteral("setProperty(\"taskview_context_mode\", tr(\"Feature Edit\"))")),
                 "PartDesign feature dialogs should publish an explicit feature-edit task context mode");
        QVERIFY2(source.contains(QStringLiteral("setProperty(\"taskview_context_title\", featureTaskContextTitle())")),
                 "PartDesign feature dialogs should publish the edited feature title to TaskView");
        QVERIFY2(source.contains(QStringLiteral("setProperty(\"taskview_summary_title\", featureTaskSummaryTitle())")),
                 "PartDesign feature dialogs should publish task summaries through the shared feature-dialog base");
        QVERIFY2(source.contains(QStringLiteral("PartDesign::Body::findBodyOf(feature)")),
                 "PartDesign feature task context should mention the owning body when available");
    }

    void test_partDesignDatumAndShapeBinderDialogs_publishTaskViewContextMetadata()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString datumPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/TaskDatumParameters.cpp"));
        QFile datumFile(datumPath);
        QVERIFY2(datumFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(datumPath));
        const QString datumSource = QString::fromUtf8(datumFile.readAll());

        QVERIFY2(datumSource.contains(QStringLiteral("setProperty(\"taskview_context_mode\", tr(\"Datum Edit\"))")),
                 "Datum dialogs should publish an explicit datum-edit task context mode");
        QVERIFY2(datumSource.contains(QStringLiteral("setProperty(\"taskview_summary_title\", ViewProvider->datumMenuText)")),
                 "Datum dialogs should publish the datum-specific summary title");
        QVERIFY2(datumSource.contains(QStringLiteral("PartDesign::Body::findBodyOf(datum)")),
                 "Datum task context should mention the owning body when available");

        const QString binderPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/TaskShapeBinder.cpp"));
        QFile binderFile(binderPath);
        QVERIFY2(binderFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(binderPath));
        const QString binderSource = QString::fromUtf8(binderFile.readAll());

        QVERIFY2(binderSource.contains(QStringLiteral("setProperty(\"taskview_context_mode\", contextMode)")),
                 "Shape binder dialogs should publish a task context mode");
        QVERIFY2(binderSource.contains(QStringLiteral("setProperty(\"taskview_summary_title\", tr(\"Shape Binder Parameters\"))")),
                 "Shape binder dialogs should publish a stable summary title");
        QVERIFY2(binderSource.contains(QStringLiteral("PartDesign::Body::findBodyOf(binder)")),
                 "Shape binder task context should mention the owning body when available");
    }

    void test_partDesignViewProviders_routeEditEntryThroughSharedHelper()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString featureProviderPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/ViewProvider.cpp"));
        QFile featureProviderFile(featureProviderPath);
        QVERIFY2(featureProviderFile.open(QIODevice::ReadOnly | QIODevice::Text),
                 qPrintable(featureProviderPath));
        const QString featureProviderSource = QString::fromUtf8(featureProviderFile.readAll());

        const QString featureDoubleClickNeedle
            = QStringLiteral("bool ViewProvider::doubleClicked()");
        const QString sharedHelperNeedle = QStringLiteral("PartDesignGui::setEdit(pcObject)");
        const QString directEditNeedle = QStringLiteral("Gui::cmdSetEdit(pcObject");
        const QString nextMethodNeedle = QStringLiteral("void ViewProvider::setupContextMenu(");

        const int featureDoubleClickPos = featureProviderSource.indexOf(featureDoubleClickNeedle);
        const int sharedHelperPos = featureProviderSource.indexOf(sharedHelperNeedle, featureDoubleClickPos);
        const int directEditPos = featureProviderSource.indexOf(directEditNeedle, featureDoubleClickPos);
        const int nextMethodPos = featureProviderSource.indexOf(nextMethodNeedle, featureDoubleClickPos);

        QVERIFY2(featureDoubleClickPos >= 0, "PartDesign ViewProvider::doubleClicked not found");
        QVERIFY2(sharedHelperPos >= 0,
                 "PartDesign ViewProvider::doubleClicked should route through PartDesignGui::setEdit");
        QVERIFY2(nextMethodPos >= 0, "PartDesign ViewProvider::setupContextMenu not found");
        QVERIFY2(sharedHelperPos < nextMethodPos,
                 "PartDesign ViewProvider::doubleClicked should call the shared helper inside the method body");
        QVERIFY2(directEditPos < 0 || directEditPos > nextMethodPos,
                 "PartDesign ViewProvider::doubleClicked should not call Gui::cmdSetEdit directly");

        const QString binderProviderPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/ViewProviderShapeBinder.cpp"));
        QFile binderProviderFile(binderProviderPath);
        QVERIFY2(binderProviderFile.open(QIODevice::ReadOnly | QIODevice::Text),
                 qPrintable(binderProviderPath));
        const QString binderProviderSource = QString::fromUtf8(binderProviderFile.readAll());

        const QString binderContextMenuNeedle
            = QStringLiteral("void ViewProviderShapeBinder::setupContextMenu(");
        const QString binderSharedHelperNeedle
            = QStringLiteral("PartDesignGui::setEdit(getObject())");
        const QString binderDirectEditNeedle
            = QStringLiteral("document->setEdit(this, ViewProvider::Default)");
        const QString binderNextNeedle
            = QStringLiteral("PROPERTY_SOURCE(PartDesignGui::ViewProviderSubShapeBinder");

        const int binderContextMenuPos = binderProviderSource.indexOf(binderContextMenuNeedle);
        const int binderSharedHelperPos
            = binderProviderSource.indexOf(binderSharedHelperNeedle, binderContextMenuPos);
        const int binderDirectEditPos
            = binderProviderSource.indexOf(binderDirectEditNeedle, binderContextMenuPos);
        const int binderNextPos = binderProviderSource.indexOf(binderNextNeedle, binderContextMenuPos);

        QVERIFY2(binderContextMenuPos >= 0,
                 "PartDesign ViewProviderShapeBinder::setupContextMenu not found");
        QVERIFY2(binderSharedHelperPos >= 0,
                 "Shape binder edit action should route through PartDesignGui::setEdit");
        QVERIFY2(binderNextPos >= 0,
                 "PartDesign ViewProviderSubShapeBinder definition not found after shape binder context menu");
        QVERIFY2(binderSharedHelperPos < binderNextPos,
                 "Shape binder context-menu edit should call the shared helper inside setupContextMenu");
        QVERIFY2(binderDirectEditPos < 0 || binderDirectEditPos > binderNextPos,
                 "Shape binder context-menu edit should not call document->setEdit directly");

        const QString baseProviderPath
            = repoRoot.filePath(QStringLiteral("src/Mod/PartDesign/Gui/ViewProviderBase.cpp"));
        QFile baseProviderFile(baseProviderPath);
        QVERIFY2(baseProviderFile.open(QIODevice::ReadOnly | QIODevice::Text),
                 qPrintable(baseProviderPath));
        const QString baseProviderSource = QString::fromUtf8(baseProviderFile.readAll());

        const QString baseDoubleClickNeedle
            = QStringLiteral("bool ViewProviderBase::doubleClicked()");
        const QString baseSharedHelperNeedle = QStringLiteral("PartDesignGui::setEdit(base)");
        const QString baseDirectEditNeedle = QStringLiteral("Gui::cmdSetEdit(base");
        const QString baseNextMethodNeedle
            = QStringLiteral("void ViewProviderBase::setupContextMenu(");

        const int baseDoubleClickPos = baseProviderSource.indexOf(baseDoubleClickNeedle);
        const int baseSharedHelperPos
            = baseProviderSource.indexOf(baseSharedHelperNeedle, baseDoubleClickPos);
        const int baseDirectEditPos
            = baseProviderSource.indexOf(baseDirectEditNeedle, baseDoubleClickPos);
        const int baseNextMethodPos = baseProviderSource.indexOf(baseNextMethodNeedle, baseDoubleClickPos);

        QVERIFY2(baseDoubleClickPos >= 0,
                 "PartDesign ViewProviderBase::doubleClicked not found");
        QVERIFY2(baseSharedHelperPos >= 0,
                 "PartDesign ViewProviderBase::doubleClicked should route through PartDesignGui::setEdit");
        QVERIFY2(baseNextMethodPos >= 0,
                 "PartDesign ViewProviderBase::setupContextMenu not found");
        QVERIFY2(baseSharedHelperPos < baseNextMethodPos,
                 "PartDesign ViewProviderBase::doubleClicked should call the shared helper inside the method body");
        QVERIFY2(baseDirectEditPos < 0 || baseDirectEditPos > baseNextMethodPos,
                 "PartDesign ViewProviderBase::doubleClicked should not call Gui::cmdSetEdit directly");
    }

    void test_sketcherDialogs_publishTaskViewContextMetadata()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString editSketchPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/TaskDlgEditSketch.cpp"));
        QFile editSketchFile(editSketchPath);
        QVERIFY2(editSketchFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(editSketchPath));
        const QString editSketchSource = QString::fromUtf8(editSketchFile.readAll());

        QVERIFY2(editSketchSource.contains(QStringLiteral("void TaskDlgEditSketch::updateTaskViewMetadata()")),
                 "Sketcher edit dialog should centralize task-view metadata publication");
        QVERIFY2(editSketchSource.contains(QStringLiteral("setProperty(\"taskview_context_mode\", tr(\"Sketch Edit\"))")),
                 "Sketcher edit dialog should publish an explicit sketch-edit context mode");
        QVERIFY2(editSketchSource.contains(QStringLiteral("setProperty(\"taskview_summary_title\", tr(\"Sketch Editing Tools\"))")),
                 "Sketcher edit dialog should publish a stable editing summary title");

        const QString validationPath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/TaskSketcherValidation.cpp"));
        QFile validationFile(validationPath);
        QVERIFY2(validationFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(validationPath));
        const QString validationSource = QString::fromUtf8(validationFile.readAll());

        QVERIFY2(validationSource.contains(QStringLiteral("setProperty(\"taskview_context_mode\", tr(\"Sketch Validation\"))")),
                 "Sketcher validation dialog should publish a validation-specific task context mode");
        QVERIFY2(validationSource.contains(QStringLiteral("setProperty(\"taskview_validation_level\", QStringLiteral(\"info\"))")),
                 "Sketcher validation dialog should publish a default validation banner");
        QVERIFY2(validationSource.contains(QStringLiteral("setProperty(\"taskview_summary_title\", tr(\"Sketch Diagnostics\"))")),
                 "Sketcher validation dialog should publish a diagnostics summary title");
    }

    void test_partDesignAttachmentSketchFlow_usesSketchWorkflowViewportNormalization()  // NOLINT
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

        const QString attachmentNeedle
            = QStringLiteral("void createSketchAndShowAttachment()");
        const QString prepareNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(guidocument);");
        const QString acceptPrepareNeedle
            = QStringLiteral("SketchWorkflowController::prepareSketchEditViewport(guiDocument);");
        const QString showAttachmentNeedle
            = QStringLiteral("vps->showAttachmentEditor(onAccept, onReject);");
        const QString setEditNeedle
            = QStringLiteral("PartDesignGui::setEdit(sketch, partDesignBody);");

        const int attachmentPos = source.indexOf(attachmentNeedle);
        const int preparePos = source.indexOf(prepareNeedle, attachmentPos);
        const int acceptPreparePos = source.indexOf(acceptPrepareNeedle, preparePos + 1);
        const int setEditPos = source.indexOf(setEditNeedle, attachmentPos);
        const int showAttachmentPos = source.indexOf(showAttachmentNeedle, attachmentPos);

        QVERIFY2(attachmentPos >= 0, "PartDesign attachment sketch helper not found");
        QVERIFY2(preparePos >= 0,
                 "PartDesign attachment sketch flow should normalize the viewport before showing the attachment editor");
        QVERIFY2(showAttachmentPos >= 0, "Attachment editor launch missing in PartDesign sketch workflow");
        QVERIFY2(acceptPreparePos >= 0,
                 "PartDesign attachment accept flow should re-normalize the viewport before setEdit");
        QVERIFY2(setEditPos >= 0, "PartDesign attachment accept flow setEdit call missing");
        QVERIFY2(preparePos < showAttachmentPos,
                 "Viewport normalization should happen before the attachment editor is shown");
        QVERIFY2(acceptPreparePos < setEditPos,
                 "Attachment accept flow should normalize the viewport before setEdit");
    }

    void test_partDesignSketchWorkflow_respectsAttachmentPreference()  // NOLINT
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

        const QString findSupportNeedle = QStringLiteral("void tryFindSupport()");
        const QString prefNeedle = QStringLiteral("GetBool(\"NewSketchUseAttachmentDialog\", false)");
        const QString attachmentNeedle = QStringLiteral("createSketchAndShowAttachment();");
        const QString planePickNeedle = QStringLiteral("findAndSelectPlane();");

        const int findSupportPos = source.indexOf(findSupportNeedle);
        const int prefPos = source.indexOf(prefNeedle, findSupportPos);
        const int attachmentPos = source.indexOf(attachmentNeedle, findSupportPos);
        const int planePickPos = source.indexOf(planePickNeedle, findSupportPos);

        QVERIFY2(findSupportPos >= 0, "PartDesign sketch support-selection helper not found");
        QVERIFY2(prefPos >= 0,
                 "PartDesign sketch workflow should read the attachment-dialog preference before choosing a support flow");
        QVERIFY2(attachmentPos >= 0,
                 "PartDesign sketch workflow should offer the attachment-dialog path when the preference is enabled");
        QVERIFY2(planePickPos >= 0,
                 "PartDesign sketch workflow should offer the plane-pick path when the attachment-dialog preference is disabled");
        QVERIFY2(prefPos < attachmentPos,
                 "Attachment preference should be resolved before choosing the attachment flow");
        QVERIFY2(attachmentPos < planePickPos,
                 "Attachment branch should be evaluated before the plane-pick fallback");
    }

    void test_partDesignPythonCommands_useSketchWorkflowPythonBridge()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const auto verifyPythonBridge = [&repoRoot](const QString& relativePath) {
            const QString filePath = repoRoot.filePath(relativePath);
            QFile file(filePath);
            QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(filePath));
            const QString source = QString::fromUtf8(file.readAll());

            QVERIFY2(source.contains(QStringLiteral("FreeCADGui.addModule(\"SketcherGui\")")),
                     qPrintable(relativePath + QStringLiteral(" should import SketcherGui for canonical sketch entry")));
            QVERIFY2(source.contains(QStringLiteral("SketcherGui.enterSketchEdit(App.ActiveDocument.ActiveObject.Name)")),
                     qPrintable(relativePath + QStringLiteral(" should use SketcherGui.enterSketchEdit for canonical sketch entry")));
            QVERIFY2(!source.contains(QStringLiteral("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name,0)")),
                     qPrintable(relativePath + QStringLiteral(" should not call Gui.activeDocument().setEdit directly")));
        };

        verifyPythonBridge(QStringLiteral("src/Mod/PartDesign/SprocketFeature.py"));
        verifyPythonBridge(QStringLiteral("src/Mod/PartDesign/InvoluteGearFeature.py"));
    }

    void test_sketcherGuiModule_exposesCanonicalPythonSketchBridge()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // PartDesign
        QVERIFY(repoRoot.cdUp());  // Mod
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString modulePath
            = repoRoot.filePath(QStringLiteral("src/Mod/Sketcher/Gui/AppSketcherGui.cpp"));
        QFile file(modulePath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(modulePath));
        const QString source = QString::fromUtf8(file.readAll());

        QVERIFY2(source.contains(QStringLiteral("add_varargs_method(")),
                 "SketcherGui module should expose Python-callable methods");
        QVERIFY2(source.contains(QStringLiteral("\"enterSketchEdit\"")),
                 "SketcherGui module should expose enterSketchEdit");
        QVERIFY2(source.contains(QStringLiteral("SketchWorkflowEntryPoint::PythonBridge")),
                 "SketcherGui.enterSketchEdit should route through the canonical sketch workflow controller");
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
