// SPDX-License-Identifier: LGPL-2.1-or-later

#include <QScrollArea>
#include <QScrollBar>
#include <QTabBar>
#include <QTabWidget>
#include <QTest>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QWidget>

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
};

// NOLINTEND(readability-magic-numbers)

QTEST_MAIN(testRibbonBarSequence)

#include "RibbonBarSequence.moc"
