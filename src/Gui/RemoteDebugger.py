# /******************************************************************************
# *   Copyright (c) 2020 Werner Mayer <wmayer[at]users.sourceforge.net>        *
# *                                                                            *
# *   This file is part of the FreeCAD CAx development system.                 *
# *                                                                            *
# *   This library is free software; you can redistribute it and/or            *
# *   modify it under the terms of the GNU Library General Public              *
# *   License as published by the Free Software Foundation; either             *
# *   version 2 of the License, or (at your option) any later version.         *
# *                                                                            *
# *   This library  is distributed in the hope that it will be useful,         *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of           *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            *
# *   GNU Library General Public License for more details.                     *
# *                                                                            *
# *   You should have received a copy of the GNU Library General Public        *
# *   License along with this library; see the file COPYING.LIB. If not,       *
# *   write to the Free Software Foundation, Inc., 59 Temple Place,            *
# *   Suite 330, Boston, MA  02111-1307, USA                                   *
# *                                                                            *
# ******************************************************************************/


import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui

from RemoteDebuggerService import attach_debugger, read_preferences


class RemoteDebugger:
    def __init__(self, parent=None):
        ui = App.getHomePath() + "Ext/freecad/gui/RemoteDebugger.ui"
        self.dialog = Gui.PySideUic.loadUi(ui)
        self.dialog.buttonBox.accepted.connect(self.accept)
        self.dialog.buttonBox.rejected.connect(self.reject)

        self.prefs = App.ParamGet("User parameter:BaseApp/Macro/Debugger")
        settings = read_preferences(self.prefs)
        self.dialog.tabWidget.setCurrentIndex(settings["tab_index"])
        self.dialog.lineEditAddress.setText(settings["address"])
        self.dialog.spinBoxPort.setValue(settings["port"])

    def accept(self):
        try:
            attach_debugger(
                {
                    "tab_index": self.dialog.tabWidget.currentIndex(),
                    "password": self.dialog.lineEditPassword.text(),
                    "address": self.dialog.lineEditAddress.text(),
                    "port": self.dialog.spinBoxPort.value(),
                },
                self.prefs,
            )

        except Exception as e:
            QtGui.QMessageBox.warning(self.dialog, "Failed to attach", str(e))

        self.dialog.accept()

    def reject(self):
        self.dialog.reject()

    def exec_(self):
        self.dialog.exec_()


def attachToRemoteDebugger():
    dlg = RemoteDebugger(Gui.getMainWindow())
    dlg.exec_()
