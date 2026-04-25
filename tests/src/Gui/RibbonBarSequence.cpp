// SPDX-License-Identifier: LGPL-2.1-or-later

#include <QScrollArea>
#include <QScrollBar>
#include <QTabBar>
#include <QTabWidget>
#include <QTest>
#include <QDir>
#include <QFile>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QWidget>
#include <QFontMetrics>

#include "Gui/RibbonBar.h"
#include <src/App/InitApplication.h>

// NOLINTBEGIN(readability-magic-numbers)

class testRibbonBarSequence: public QObject
{
    Q_OBJECT

public:
    testRibbonBarSequence()
    {
        tests::initApplication();
    }

private Q_SLOTS:

    void init() {}

    void cleanup() {}

    void test_DensityLayoutUsesNaturalWidthAndSpacing()  // NOLINT
    {
        QWidget host;
        host.resize(640, 220);
        auto* hostLayout = new QVBoxLayout(&host);
        hostLayout->setContentsMargins(0, 0, 0, 0);

        auto* page = new Gui::RibbonTabPage(&host);
        hostLayout->addWidget(page);

        auto* panel = new Gui::RibbonPanel(QStringLiteral("Model"), page);
        panel->addButton(new Gui::RibbonButton(QStringLiteral("A"), Gui::RibbonButton::Large, panel));
        panel->addButton(new Gui::RibbonButton(QStringLiteral("B"), Gui::RibbonButton::Small, panel));
        panel->addButton(new Gui::RibbonButton(QStringLiteral("C"), Gui::RibbonButton::Small, panel));
        panel->addButton(new Gui::RibbonButton(QStringLiteral("D"), Gui::RibbonButton::Small, panel));
        page->addPanel(panel);

        host.show();
        QCoreApplication::processEvents();

        auto* scrollArea = page->findChild<QScrollArea*>();
        QVERIFY(scrollArea != nullptr);
        QVERIFY(!scrollArea->widgetResizable());

        auto* buttonArea = panel->findChild<QWidget*>();
        QVERIFY(buttonArea != nullptr);
        auto* panelLayout = qobject_cast<QHBoxLayout*>(buttonArea->layout());
        QVERIFY(panelLayout != nullptr);
        QVERIFY(panelLayout->spacing() >= 6);
    }

    void test_AddPanelsOverflowThenClearSequence()  // NOLINT
    {
        QWidget host;
        host.resize(220, 240);

        auto* hostLayout = new QVBoxLayout(&host);
        hostLayout->setContentsMargins(0, 0, 0, 0);

        auto* page = new Gui::RibbonTabPage(&host);
        hostLayout->addWidget(page);

        host.show();
        QCoreApplication::processEvents();

        auto makePanel = [page](const QString& title) {
            auto* panel = new Gui::RibbonPanel(title, page);
            panel->addButton(
                new Gui::RibbonButton(QStringLiteral("PrimaryAction"), Gui::RibbonButton::Large, panel)
            );
            panel->addButton(
                new Gui::RibbonButton(QStringLiteral("SecondaryAction"), Gui::RibbonButton::Large, panel)
            );
            panel->addButton(
                new Gui::RibbonButton(QStringLiteral("SmallActionOne"), Gui::RibbonButton::Small, panel)
            );
            panel->addButton(
                new Gui::RibbonButton(QStringLiteral("SmallActionTwo"), Gui::RibbonButton::Small, panel)
            );
            panel->addButton(
                new Gui::RibbonButton(QStringLiteral("SmallActionThree"), Gui::RibbonButton::Small, panel)
            );
            return panel;
        };

        // Sequence step 1: add multiple wide panels, forcing horizontal overflow.
        page->addPanel(makePanel(QStringLiteral("Create")));
        page->addPanel(makePanel(QStringLiteral("Modify")));
        page->addPanel(makePanel(QStringLiteral("Inspect")));
        QCoreApplication::processEvents();
        auto* scrollArea = page->findChild<QScrollArea*>();
        QVERIFY(scrollArea != nullptr);

        const int contentWidthBefore = scrollArea->widget()->sizeHint().width();
        const int viewportWidth = scrollArea->viewport()->width();
        QVERIFY(contentWidthBefore > viewportWidth);

        // Sequence step 2: clear panels and verify overflow is removed.
        page->clearPanels();
        QCoreApplication::processEvents();
        QCOMPARE(page->panels().size(), 0);
        const int contentWidthAfter = scrollArea->widget()->sizeHint().width();
        QVERIFY(contentWidthAfter < contentWidthBefore);
    }

    void test_LargeButtonMultilineLabelGetsEnoughWidth()  // NOLINT
    {
        Gui::RibbonButton button(QStringLiteral("cmd"), Gui::RibbonButton::Large);
        button.setText(QStringLiteral("LongLabel\nSecondLine"));

        QFontMetrics fm(button.font());
        const int expectedMin = qMax(
            fm.horizontalAdvance(QStringLiteral("LongLabel")),
            fm.horizontalAdvance(QStringLiteral("SecondLine"))
        ) + 16;

        QVERIFY(button.sizeHint().width() >= expectedMin);
    }

    void test_BackstageHideRestoresWorkbenchChrome()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString backstagePath = repoRoot.filePath(QStringLiteral("src/Gui/BackstageView.cpp"));
        QFile file(backstagePath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(backstagePath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString hideEventNeedle = QStringLiteral("void BackstageView::hideEvent(QHideEvent* event)");
        const QString ribbonNeedle = QStringLiteral("ribbon->show();");
        const QString refreshNeedle = QStringLiteral("Application::Instance->refreshActiveWorkbench();");

        const int hideEventPos = source.indexOf(hideEventNeedle);
        const int ribbonPos = source.indexOf(ribbonNeedle, hideEventPos);
        const int refreshPos = source.indexOf(refreshNeedle, hideEventPos);

        QVERIFY2(hideEventPos >= 0, "BackstageView hideEvent override missing");
        QVERIFY2(ribbonPos >= 0, "BackstageView hideEvent should restore ribbon visibility");
        QVERIFY2(refreshPos >= 0,
             "BackstageView hideEvent should refresh the active workbench through Gui::Application");
        QVERIFY2(ribbonPos < refreshPos,
             "BackstageView hideEvent should restore ribbon visibility before workbench shell refresh");
    }

    void test_RibbonShellButtonRoutesToBackstage()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString ribbonPath = repoRoot.filePath(QStringLiteral("src/Gui/RibbonBar.cpp"));
        QFile file(ribbonPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(ribbonPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString buttonNeedle
            = QStringLiteral("applicationButton->setObjectName(QStringLiteral(\"ribbonApplicationButton\"))");
        const QString connectNeedle
            = QStringLiteral("connect(applicationButton, &QToolButton::clicked, this, [this]() {");
        const QString backstageNeedle = QStringLiteral("openBackstage();");

        const int buttonPos = source.indexOf(buttonNeedle);
        const int connectPos = source.indexOf(connectNeedle, buttonPos);
        const int backstagePos = source.indexOf(backstageNeedle, connectPos);

        QVERIFY2(buttonPos >= 0,
                 "RibbonBar should expose an application shell button in the header");
        QVERIFY2(connectPos >= 0,
                 "RibbonBar application shell button should be connected to a click handler");
        QVERIFY2(backstagePos >= 0,
                 "RibbonBar application shell button should route through openBackstage");
    }

    void test_SketcherToolbarsRouteToSketchTab()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString ribbonPath = repoRoot.filePath(QStringLiteral("src/Gui/RibbonBar.cpp"));
        QFile file(ribbonPath);
        QVERIFY2(file.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(ribbonPath));
        const QString source = QString::fromUtf8(file.readAll());

        const QString categorizeNeedle = QStringLiteral("QString RibbonBar::categorizeToolbar(const QString& tbName) const");
        const int categorizePos = source.indexOf(categorizeNeedle);
        QVERIFY2(categorizePos >= 0, "RibbonBar::categorizeToolbar definition missing");

        const int sketchRulePos = source.indexOf(
            QStringLiteral("\"Edit Mode\""), categorizePos);
        QVERIFY2(sketchRulePos >= 0,
                 "Sketch routing should explicitly cover Sketcher edit-mode toolbar names");
        QVERIFY2(source.indexOf(QStringLiteral("\"Geometries\""), sketchRulePos) >= 0,
                 "Sketch routing should explicitly cover Sketcher geometry toolbar names");
        QVERIFY2(source.indexOf(QStringLiteral("\"Constraints\""), sketchRulePos) >= 0,
                 "Sketch routing should explicitly cover Sketcher constraint toolbar names");
        QVERIFY2(source.indexOf(QStringLiteral("\"Sketcher Tools\""), sketchRulePos) >= 0,
                 "Sketch routing should explicitly cover Sketcher helper toolbar names");
        QVERIFY2(source.indexOf(QStringLiteral("\"B-Spline Tools\""), sketchRulePos) >= 0,
                 "Sketch routing should explicitly cover Sketcher B-Spline toolbar names");
        QVERIFY2(source.indexOf(QStringLiteral("\"Visual Helpers\""), sketchRulePos) >= 0,
                 "Sketch routing should explicitly cover Sketcher visual toolbar names");

        const int sketchReturnPos = source.indexOf(QStringLiteral("return tr(\"Sketch\");"), sketchRulePos);
        QVERIFY2(sketchReturnPos >= 0,
                 "Sketch toolbar routing should resolve to the Sketch ribbon tab");

        const int toolsRulePos = source.indexOf(QStringLiteral("return tr(\"Tools\");"), sketchRulePos);
        QVERIFY2(toolsRulePos > sketchReturnPos,
                 "Sketch routing must be evaluated before the generic Tools fallback");
    }

    void test_ToggleRibbonUsesSharedWorkbenchRefresh()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString commandViewPath = repoRoot.filePath(QStringLiteral("src/Gui/CommandView.cpp"));
        QFile commandViewFile(commandViewPath);
        QVERIFY2(commandViewFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(commandViewPath));
        const QString commandViewSource = QString::fromUtf8(commandViewFile.readAll());

        const QString toggleNeedle
            = QStringLiteral("void StdCmdToggleRibbonBar::activated(int iMsg)");
        const int togglePos = commandViewSource.indexOf(toggleNeedle);
        QVERIFY2(togglePos >= 0, "StdCmdToggleRibbonBar::activated definition missing");

        const int refreshCallPos = commandViewSource.indexOf(
            QStringLiteral("Application::Instance->refreshActiveWorkbench();"), togglePos);
        QVERIFY2(refreshCallPos >= 0,
                 "StdCmdToggleRibbonBar should refresh shell state through Gui::Application");

        QVERIFY2(commandViewSource.indexOf(
                      QStringLiteral("getMainWindow()->activateWorkbench("), togglePos) < 0,
                 "StdCmdToggleRibbonBar should not replay MainWindow workbench activation inline");
        QVERIFY2(commandViewSource.indexOf(
                      QStringLiteral("signalActivateWorkbench("), togglePos) < 0,
                 "StdCmdToggleRibbonBar should not emit workbench activation inline");
        QVERIFY2(commandViewSource.indexOf(QStringLiteral("wb->activated();"), togglePos) < 0,
                 "StdCmdToggleRibbonBar should not call Workbench::activated inline");

        const QString appPath = repoRoot.filePath(QStringLiteral("src/Gui/Application.cpp"));
        QFile appFile(appPath);
        QVERIFY2(appFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(appPath));
        const QString appSource = QString::fromUtf8(appFile.readAll());

        const QString refreshNeedle = QStringLiteral("bool Application::refreshActiveWorkbench()");
        const int refreshPos = appSource.indexOf(refreshNeedle);
        QVERIFY2(refreshPos >= 0, "Gui::Application::refreshActiveWorkbench definition missing");
         QVERIFY2(appSource.indexOf(QStringLiteral("if (isClosing() || QApplication::closingDown())"),
                        refreshPos) >= 0,
               "refreshActiveWorkbench should no-op while the GUI is shutting down");
         QVERIFY2(appSource.indexOf(QStringLiteral("auto* mainWindow = getMainWindow();"),
                        refreshPos) >= 0,
               "refreshActiveWorkbench should resolve MainWindow once before replaying shell state");
         QVERIFY2(appSource.indexOf(QStringLiteral("if (!mainWindow)"), refreshPos) >= 0,
               "refreshActiveWorkbench should tolerate a missing MainWindow during teardown");
        QVERIFY2(appSource.indexOf(QStringLiteral("wb->activate();"), refreshPos) >= 0,
                 "refreshActiveWorkbench should rebuild the active workbench surfaces");
        QVERIFY2(appSource.indexOf(
                      QStringLiteral("mainWindow->activateWorkbench("), refreshPos) >= 0,
                 "refreshActiveWorkbench should notify MainWindow about workbench activation");
        QVERIFY2(appSource.indexOf(QStringLiteral("signalActivateWorkbench("), refreshPos) >= 0,
                 "refreshActiveWorkbench should emit the shared workbench activation signal");
        QVERIFY2(appSource.indexOf(QStringLiteral("wb->activated();"), refreshPos) >= 0,
                 "refreshActiveWorkbench should run Workbench::activated()");

        const QString macroDialogPath
            = repoRoot.filePath(QStringLiteral("src/Gui/Dialogs/DlgMacroExecuteImp.cpp"));
        QFile macroDialogFile(macroDialogPath);
        QVERIFY2(macroDialogFile.open(QIODevice::ReadOnly | QIODevice::Text),
                 qPrintable(macroDialogPath));
        const QString macroDialogSource = QString::fromUtf8(macroDialogFile.readAll());

        const QString macroRefreshNeedle
            = QStringLiteral("Application::Instance->refreshActiveWorkbench();");
        const QString macroReloadNeedle
            = QStringLiteral("dlg.exec();");
        const int macroReloadPos = macroDialogSource.indexOf(macroReloadNeedle);
        QVERIFY2(macroReloadPos >= 0, "DlgMacroExecuteImp should execute the macro dialog");
        QVERIFY2(macroDialogSource.indexOf(macroRefreshNeedle, macroReloadPos) >= 0,
                 "DlgMacroExecuteImp should refresh the active workbench through Gui::Application");
        QVERIFY2(macroDialogSource.indexOf(QStringLiteral("active->activate();"), macroReloadPos) < 0,
                 "DlgMacroExecuteImp should not reactivate the workbench inline after the dialog closes");

        const QString workbenchPyPath = repoRoot.filePath(QStringLiteral("src/Gui/WorkbenchPyImp.cpp"));
        QFile workbenchPyFile(workbenchPyPath);
        QVERIFY2(workbenchPyFile.open(QIODevice::ReadOnly | QIODevice::Text),
                 qPrintable(workbenchPyPath));
        const QString workbenchPySource = QString::fromUtf8(workbenchPyFile.readAll());

        const QString reloadActiveNeedle
            = QStringLiteral("PyObject* WorkbenchPy::reloadActive(PyObject* args)");
        const int reloadActivePos = workbenchPySource.indexOf(reloadActiveNeedle);
        QVERIFY2(reloadActivePos >= 0, "WorkbenchPy::reloadActive definition missing");
        QVERIFY2(workbenchPySource.indexOf(macroRefreshNeedle, reloadActivePos) >= 0,
                 "WorkbenchPy::reloadActive should refresh the active workbench through Gui::Application");
        QVERIFY2(workbenchPySource.indexOf(QStringLiteral("active->activate();"), reloadActivePos) < 0,
                 "WorkbenchPy::reloadActive should not reactivate the workbench inline");
    }

    void test_TaskDialogTransitionsUseSharedShellRefresh()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString controlPath = repoRoot.filePath(QStringLiteral("src/Gui/Control.cpp"));
        QFile controlFile(controlPath);
        QVERIFY2(controlFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(controlPath));
        const QString controlSource = QString::fromUtf8(controlFile.readAll());

        const QString refreshNeedle = QStringLiteral("Application::Instance->refreshActiveWorkbench();");

        const QString showNeedle = QStringLiteral("void ControlSingleton::showDialog(");
        const int showPos = controlSource.indexOf(showNeedle);
        QVERIFY2(showPos >= 0, "ControlSingleton::showDialog definition missing");
        QVERIFY2(controlSource.indexOf(refreshNeedle, showPos) >= 0,
                 "ControlSingleton::showDialog should refresh shell state through Gui::Application");

        const QString closeNeedle = QStringLiteral("void ControlSingleton::closedDialog(App::Document* attachedTo)");
        const int closePos = controlSource.indexOf(closeNeedle);
        QVERIFY2(closePos >= 0, "ControlSingleton::closedDialog definition missing");
        QVERIFY2(controlSource.indexOf(refreshNeedle, closePos) >= 0,
                 "ControlSingleton::closedDialog should refresh shell state through Gui::Application");
    }

    void test_SplitViewKeepsPersistentNaviCubeSettings()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString headerPath = repoRoot.filePath(QStringLiteral("src/Gui/SplitView3DInventor.h"));
        QFile headerFile(headerPath);
        QVERIFY2(headerFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(headerPath));
        const QString headerSource = QString::fromUtf8(headerFile.readAll());

        const QString implPath = repoRoot.filePath(QStringLiteral("src/Gui/SplitView3DInventor.cpp"));
        QFile implFile(implPath);
        QVERIFY2(implFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(implPath));
        const QString implSource = QString::fromUtf8(implFile.readAll());

        QVERIFY2(headerSource.indexOf(
                      QStringLiteral("std::vector<std::unique_ptr<NaviCubeSettings>> naviSettings;")) >= 0,
                 "AbstractSplitView should retain NaviCubeSettings observers for split viewers");

        const QString setupNeedle = QStringLiteral("void AbstractSplitView::setupSettings()");
        const int setupPos = implSource.indexOf(setupNeedle);
        QVERIFY2(setupPos >= 0, "AbstractSplitView::setupSettings definition missing");
        QVERIFY2(implSource.indexOf(QStringLiteral("naviSettings.clear();"), setupPos) >= 0,
                 "AbstractSplitView::setupSettings should reset retained NaviCubeSettings before rebuilding them");
        QVERIFY2(implSource.indexOf(QStringLiteral("auto viewerNaviSettings = std::make_unique<NaviCubeSettings>("), setupPos) >= 0,
                 "AbstractSplitView::setupSettings should allocate persistent NaviCubeSettings instances");
        QVERIFY2(implSource.indexOf(QStringLiteral("viewerNaviSettings->applySettings();"), setupPos) >= 0,
                 "AbstractSplitView::setupSettings should apply per-view NaviCube settings");
        QVERIFY2(implSource.indexOf(QStringLiteral("naviSettings.push_back(std::move(viewerNaviSettings));"), setupPos) >= 0,
                 "AbstractSplitView::setupSettings should retain each NaviCubeSettings observer");
    }

    void test_ViewerPythonWrapperExposesSplitOverlayState()  // NOLINT
    {
        QDir repoRoot(QStringLiteral(QT_TESTCASE_SOURCEDIR));
        QVERIFY(repoRoot.cdUp());  // src
        QVERIFY(repoRoot.cdUp());  // tests
        QVERIFY(repoRoot.cdUp());  // repo root

        const QString headerPath = repoRoot.filePath(QStringLiteral("src/Gui/View3DViewerPy.h"));
        QFile headerFile(headerPath);
        QVERIFY2(headerFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(headerPath));
        const QString headerSource = QString::fromUtf8(headerFile.readAll());

        const QString implPath = repoRoot.filePath(QStringLiteral("src/Gui/View3DViewerPy.cpp"));
        QFile implFile(implPath);
        QVERIFY2(implFile.open(QIODevice::ReadOnly | QIODevice::Text), qPrintable(implPath));
        const QString implSource = QString::fromUtf8(implFile.readAll());

        QVERIFY2(headerSource.indexOf(
                      QStringLiteral("Py::Object setCornerCrossVisible(const Py::Tuple& args);")) >= 0,
                 "View3DInventorViewerPy should declare setCornerCrossVisible for split-view overlay probes");
        QVERIFY2(headerSource.indexOf(
                      QStringLiteral("Py::Object isCornerCrossVisible(const Py::Tuple& args);")) >= 0,
                 "View3DInventorViewerPy should declare isCornerCrossVisible for split-view overlay probes");

        QVERIFY2(implSource.indexOf(QStringLiteral("\"setCornerCrossVisible\",")) >= 0,
                 "View3DInventorViewerPy should register setCornerCrossVisible in the Python method table");
        QVERIFY2(implSource.indexOf(QStringLiteral("\"isCornerCrossVisible\",")) >= 0,
                 "View3DInventorViewerPy should register isCornerCrossVisible in the Python method table");

        const QString setNeedle = QStringLiteral("Py::Object View3DInventorViewerPy::setCornerCrossVisible(const Py::Tuple& args)");
        const int setPos = implSource.indexOf(setNeedle);
        QVERIFY2(setPos >= 0,
                 "View3DInventorViewerPy::setCornerCrossVisible definition missing");
        QVERIFY2(implSource.indexOf(QStringLiteral("_viewer->setFeedbackVisibility(Base::asBoolean(visible));"), setPos) >= 0,
                 "setCornerCrossVisible should route through the viewer feedback visibility");

        const QString getNeedle = QStringLiteral("Py::Object View3DInventorViewerPy::isCornerCrossVisible(const Py::Tuple& args)");
        const int getPos = implSource.indexOf(getNeedle);
        QVERIFY2(getPos >= 0,
                 "View3DInventorViewerPy::isCornerCrossVisible definition missing");
        QVERIFY2(implSource.indexOf(QStringLiteral("bool visible = _viewer->isFeedbackVisible();"), getPos) >= 0,
                 "isCornerCrossVisible should report the viewer feedback visibility");
    }
};

// NOLINTEND(readability-magic-numbers)

QTEST_MAIN(testRibbonBarSequence)

#include "RibbonBarSequence.moc"
