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
        const QString activateNeedle = QStringLiteral("workbench->activate();");

        const int hideEventPos = source.indexOf(hideEventNeedle);
        const int ribbonPos = source.indexOf(ribbonNeedle, hideEventPos);
        const int activatePos = source.indexOf(activateNeedle, hideEventPos);

        QVERIFY2(hideEventPos >= 0, "BackstageView hideEvent override missing");
        QVERIFY2(ribbonPos >= 0, "BackstageView hideEvent should restore ribbon visibility");
        QVERIFY2(activatePos >= 0, "BackstageView hideEvent should reactivate the active workbench");
        QVERIFY2(ribbonPos < activatePos,
                 "BackstageView hideEvent should restore ribbon visibility before workbench reactivation");
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
};

// NOLINTEND(readability-magic-numbers)

QTEST_MAIN(testRibbonBarSequence)

#include "RibbonBarSequence.moc"
